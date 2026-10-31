from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import numpy as np
from askai.core.component.faces.index import FaceIndex, FaceRecord
from askai.core.component.faces.migration import migrate


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.source = root / 'chroma.sqlite3'
        self.photo = root / 'face.jpg'
        self.photo.write_bytes(b'original photo')
        with sqlite3.connect(self.source) as db:
            db.executescript('''
                CREATE TABLE collections (id TEXT, name TEXT);
                CREATE TABLE segments (id TEXT, collection TEXT);
                CREATE TABLE embeddings (id INTEGER, segment_id TEXT, embedding_id TEXT);
                CREATE TABLE embedding_metadata (id INTEGER, key TEXT, string_value TEXT);
                INSERT INTO collections VALUES ('c','image_store');
                INSERT INTO segments VALUES ('s','c');
                INSERT INTO embeddings VALUES (1,'s','face1');
            ''')
            db.executemany('INSERT INTO embedding_metadata VALUES (1,?,?)', [
                ('img_category', 'faces'), ('img_path', str(self.photo)),
                ('img_caption', 'Stored description'), ('identity_name', 'Hugo'),
            ])
        self.index = FaceIndex(root / 'sface.sqlite3')
        self.models = Mock()
        self.models.detect.return_value = [SimpleNamespace(vector=np.ones(128))]
        self.image = patch('askai.core.component.faces.migration.cv2.imread', return_value=np.zeros((10, 10, 3))).start()
        self.addCleanup(patch.stopall)

    def test_recomputes_preserving_source_names_and_paths_and_is_idempotent(self):
        before = self.source.read_bytes()
        report = migrate(self.source, self.index, self.models)
        self.assertEqual(report['indexed'], 1)
        self.assertEqual(self.index.records()[0].name, 'Hugo')
        self.assertEqual(self.index.records()[0].path, str(self.photo))
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(self.photo.read_bytes(), b'original photo')
        self.assertEqual(migrate(self.source, self.index, self.models), report)
        self.models.detect.assert_called_once()

    def test_pending_preserves_name_and_retry_rebuild_keeps_new_enrollments(self):
        self.models.detect.return_value = []
        report = migrate(self.source, self.index, self.models)
        self.assertEqual(report['skipped'][0]['reason'], 'no_face')
        with sqlite3.connect(self.index.path) as db:
            self.assertEqual(db.execute('SELECT name,caption FROM pending_faces').fetchone(), ('Hugo', 'Stored description'))
        self.index.add([FaceRecord('new', '/new.png', 'Maria', '', np.ones(128))])
        self.models.detect.return_value = [SimpleNamespace(vector=np.ones(128))]
        migrate(self.source, self.index, self.models, rebuild=True)
        self.assertEqual({r.name for r in self.index.records()}, {'Hugo', 'Maria'})
        with sqlite3.connect(self.index.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM pending_faces').fetchone()[0], 0)

    def test_multiple_faces_not_assigned_one_person(self):
        self.models.detect.return_value *= 2
        report = migrate(self.source, self.index, self.models)
        self.assertEqual(report['skipped'][0]['reason'], 'multiple_faces')
        self.assertEqual(self.index.records(), [])

    def test_model_error_does_not_mark_migration_complete(self):
        self.models.detect.side_effect = RuntimeError('model error')
        with self.assertRaises(RuntimeError):
            migrate(self.source, self.index, self.models)
        with sqlite3.connect(self.index.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM migrations').fetchone()[0], 0)
