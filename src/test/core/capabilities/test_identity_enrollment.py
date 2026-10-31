"""Enrollment uses synthetic images and an isolated store, never user photos."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

import cv2
import numpy as np

from askai.core.component.identity_enrollment import IdentityEnrollment, EnrollmentFace

from askai.core.component.faces.models import DetectedFace
from askai.core.component.faces.selections import FaceAction, FaceSelection


class EnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.workspace = TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.camera = Mock()
        self.camera.detect.return_value = [
            DetectedFace((5, 5, 30, 30), np.zeros((112, 112, 3), np.uint8), np.ones(128)),
            DetectedFace((60, 30, 25, 25), np.zeros((112, 112, 3), np.uint8), np.ones(128)),
        ]
        self.caption = Mock(return_value='{"env_description": "A face"}')
        self.store = Mock()
        self.store.identities.return_value = []
        self.service = IdentityEnrollment(self.camera, self.store, self.root / 'faces', self.caption)
        self.source = self.root / 'source.png'
        self.photo = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(self.source), self.photo)

    def test_prepares_numbered_preview_and_captioned_crops_without_enrolling(self):
        result = self.service.prepare(str(self.source), self.root)
        self.assertEqual([face.label for face in result.faces], [1, 2])
        self.assertEqual([face.caption for face in result.faces], ['A face', 'A face'])
        self.assertEqual(cv2.imread(str(result.faces[0].path)).shape[:2], (112, 112))
        self.assertTrue(np.any(cv2.imread(str(result.preview)) != self.photo))
        self.assertTrue(np.array_equal(cv2.imread(str(self.source)), self.photo))
        self.assertEqual(self.caption.call_count, 2)
        self.store.apply_samples.assert_not_called()

    def test_names_are_metadata_and_blank_names_skip_faces(self):
        prepared = self.service.prepare(str(self.source), self.root)
        result = self.service.save([FaceSelection(prepared.faces[0], FaceAction.NEW, '  Hugo Júnior  '), FaceSelection(prepared.faces[1], FaceAction.SKIP)])
        self.assertEqual(result[0]['name'], 'Hugo Júnior')
        self.assertEqual(len(result), 1)
        saved = self.store.apply_samples.call_args.args[0][0]
        self.assertEqual(saved.name, 'Hugo Júnior')
        self.assertEqual(saved.caption, 'A face')
        self.assertTrue(Path(saved.path).is_file())
        self.assertNotIn('Hugo', saved.path)

    def test_store_failure_removes_only_new_owned_files(self):
        prepared = self.service.prepare(str(self.source), self.root)
        self.store.apply_samples.side_effect = RuntimeError('database unavailable')
        with self.assertRaises(RuntimeError):
            self.service.save([FaceSelection(prepared.faces[0], FaceAction.NEW, 'Hugo')])
        self.assertEqual(list((self.root / 'faces').iterdir()), [])
        self.assertTrue(self.source.exists())

    def test_no_faces_no_caption_or_store(self):
        self.camera.detect.return_value = []
        prepared = self.service.prepare(str(self.source), self.root)
        self.assertEqual(prepared.faces, [])
        self.assertEqual(self.service.save([]), [])
        self.caption.assert_not_called()
        self.store.apply_samples.assert_not_called()

    def test_bad_image_and_caption_fail_without_enrollment(self):
        self.source.write_text('not an image')
        with self.assertRaises(ValueError):
            self.service.prepare(str(self.source), self.root)
        cv2.imwrite(str(self.source), self.photo)
        self.caption.return_value = '{}'
        with self.assertRaises(KeyError):
            self.service.prepare(str(self.source), self.root)
        self.store.apply_samples.assert_not_called()

    def test_invalid_names_rejected_before_writing(self):
        for name in ('x' * 121, 'Hugo\nOther', 'Hugo\x1b', None):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.service.save([FaceSelection(EnrollmentFace(1, self.source, 'Face', np.ones(128)), FaceAction.NEW, name)])
        self.store.apply_samples.assert_not_called()

    def test_default_enrollment_does_not_require_blip(self):
        service = IdentityEnrollment(self.camera, self.store, self.root / 'faces')
        prepared = service.prepare(str(self.source), self.root)
        self.assertEqual([face.caption for face in prepared.faces], ['', ''])
        self.caption.assert_not_called()
