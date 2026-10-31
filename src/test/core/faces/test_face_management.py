from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock
import cv2
import numpy as np

from askai.core.component.faces.index import FaceIndex, FaceRecord
from askai.core.component.faces.selections import FaceSelection, FaceAction
from askai.core.component.identity_enrollment import IdentityEnrollment, EnrollmentFace


class ManagementTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.index = FaceIndex(self.root / 'index.sqlite3')
        self.vector = np.ones(128, np.float32)
        for record_id, name in [('migrated-a', 'Hugo'), ('b', 'Hugo'), ('c', 'Outro cadastro')]:
            path = self.root / f'{record_id}.png'
            cv2.imwrite(str(path), np.zeros((112, 112, 3), np.uint8))
            self.index.add([FaceRecord(record_id, str(path), name, '', self.vector)])
        self.service = IdentityEnrollment(Mock(), self.index, self.root / 'faces')

    def test_merge_reassigns_sample_without_copying_or_losing_other_samples(self):
        prepared = self.service.review(self.root)
        selected = next(face for face in prepared.faces if face.source_id == 'c')
        self.service.save([FaceSelection(selected, FaceAction.MERGE, '  HUGO  ')])
        self.assertEqual(self.index.identities(), [{'name': 'Hugo', 'samples': 3}])
        self.assertEqual(len(self.index.records()), 3)
        self.assertEqual(next(r for r in self.index.records() if r.id == 'c').path, str(selected.path))
        self.assertEqual(len(list((self.root / 'faces').iterdir())), 0)

    def test_replace_removes_old_samples_once_and_keeps_all_selected_new_ones(self):
        prepared = self.service.review(self.root)
        face = next(face for face in prepared.faces if face.source_id == 'c')
        extra = EnrollmentFace(9, face.path, '', self.vector)
        self.service.save([FaceSelection(face, FaceAction.REPLACE, 'Hugo'),
                           FaceSelection(extra, FaceAction.MERGE, 'Hugo')])
        self.assertEqual(self.index.identities(), [{'name': 'Hugo', 'samples': 2}])
        self.assertNotIn('b', [r.id for r in self.index.records()])
        self.assertTrue((self.root / 'migrated-a.png').exists())
        self.assertTrue((self.root / 'b.png').exists())

    def test_skip_changes_nothing(self):
        before = self.index.path.read_bytes()
        self.service.save([FaceSelection(self.service.review(self.root).faces[0], FaceAction.SKIP)])
        self.assertEqual(self.index.path.read_bytes(), before)

    def test_new_identity_rejects_case_or_space_duplicates(self):
        face = self.service.review(self.root).faces[0]
        with self.assertRaises(ValueError):
            self.service.save([FaceSelection(face, FaceAction.NEW, '  HUGO ')])
        with self.assertRaises(ValueError):
            self.service.save([FaceSelection(face, FaceAction.MERGE, 'Missing')])
        with self.assertRaises(ValueError):
            self.service.save([FaceSelection(face, FaceAction.REPLACE, 'Missing')])
        self.assertEqual(len(self.index.records()), 3)

    def test_new_identity_and_merge_can_share_one_batch(self):
        faces = self.service.review(self.root).faces
        self.service.save([FaceSelection(faces[0], FaceAction.NEW, 'Pessoa'),
                           FaceSelection(faces[1], FaceAction.MERGE, 'Pessoa')])
        self.assertIn({'name': 'Pessoa', 'samples': 2}, self.index.identities())

    def test_rebuild_does_not_resurrect_replaced_or_overwrite_relabelled_samples(self):
        prepared = self.service.review(self.root)
        selected = next(face for face in prepared.faces if face.source_id == 'migrated-a')
        self.service.save([FaceSelection(selected, FaceAction.MERGE, 'Outro cadastro')])
        self.index.add([FaceRecord('migrated-a', str(selected.path), 'Hugo', '', self.vector)], ('migration', '{}'))
        self.assertEqual(next(r.name for r in self.index.records() if r.id == 'migrated-a'), 'Outro cadastro')
        other = next(face for face in prepared.faces if face.source_id == 'b')
        self.service.save([FaceSelection(other, FaceAction.REPLACE, 'Outro cadastro')])
        self.index.add([FaceRecord('migrated-a', str(selected.path), 'Hugo', '', self.vector)], ('migration', '{}'))
        self.assertNotIn('migrated-a', [r.id for r in self.index.records()])

    def test_preview_numbers_all_existing_samples_without_detection(self):
        prepared = self.service.review(self.root)
        self.assertEqual([face.label for face in prepared.faces], [1, 2, 3])
        self.assertEqual(cv2.imread(str(prepared.preview)).shape[:2], (180, 720))
        self.service._models.detect.assert_not_called()

    def test_failed_replacement_rolls_back_removed_samples(self):
        with self.assertRaises(ValueError):
            self.index.apply_samples([FaceRecord('new', '/new', 'Hugo', '', np.zeros(128))], {'Hugo'})
        self.assertEqual(len(self.index.records()), 3)
