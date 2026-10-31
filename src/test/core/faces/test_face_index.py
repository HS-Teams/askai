from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import numpy as np
from askai.core.component.faces.index import FaceIndex, FaceRecord


def vector(index=0):
    value = np.zeros(128, np.float32)
    value[index] = 1
    return value


class FaceIndexTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'faces.sqlite3'
        self.index = FaceIndex(self.path)

    def test_restart_preserves_names_photos_and_vectors(self):
        self.index.add([FaceRecord('a', '/photos/a.png', 'Hugo Júnior', 'A face', vector())])
        loaded = FaceIndex(self.path)
        record = loaded.records()[0]
        self.assertEqual((record.name, record.path, record.caption), ('Hugo Júnior', '/photos/a.png', 'A face'))
        self.assertEqual(loaded.match([vector()], 0.363)[0]['name'], 'Hugo Júnior')
        self.assertEqual(loaded.match([vector(1)], 0.363)[0]['status'], 'unknown')

    def test_batch_failure_rolls_back_all_faces(self):
        self.index.add([FaceRecord('a', '/a', 'Hugo', '', vector())])
        with self.assertRaises(Exception):
            self.index.add([FaceRecord('b', '/b', 'Maria', '', vector(1)), FaceRecord('a', '/c', 'Other', '', vector())])
        self.assertEqual([r.id for r in self.index.records()], ['a'])

    def test_multiple_faces_and_empty_index(self):
        self.assertEqual(len(self.index.match([vector(), vector(1)], 0.5)), 2)
        self.index.add([FaceRecord('a', '/a', 'Hugo', '', vector()), FaceRecord('b', '/b', 'Maria', '', vector(1))])
        self.assertEqual([r['name'] for r in self.index.match([vector(1), vector()], 0.5)], ['Maria', 'Hugo'])

    def test_invalid_vectors_and_thresholds_rejected(self):
        for value in (np.zeros(128), np.ones(512), np.full(128, np.nan)):
            with self.assertRaises(ValueError):
                self.index.add([FaceRecord('a', '/a', 'Hugo', '', value)])
        for threshold in (float('nan'), 2, -2):
            with self.assertRaises(ValueError):
                self.index.match([], threshold)

    def test_unlabelled_records_never_infer_names_from_captions(self):
        self.index.add([FaceRecord('a', '/a', None, 'Looks like Hugo', vector())])
        result = self.index.match([vector()], 0.5)[0]
        self.assertIsNone(result['name'])
        self.assertEqual(result['status'], 'unlabelled')
