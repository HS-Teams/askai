from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
import unittest
from unittest.mock import Mock, patch
import numpy as np
from askai.core.component.faces.models import FaceModels, model_path


class ModelsTests(unittest.TestCase):
    def test_aligns_using_landmarks_before_encoding_and_orders_labels(self):
        models = FaceModels.__new__(FaceModels)
        models._lock = Lock()
        models._detector, models._recognizer = Mock(), Mock()
        high, low = np.zeros(15, np.float32), np.zeros(15, np.float32)
        high[:4] = [5, 10, 20, 20]
        low[:4] = [30, 50, 20, 20]
        models._detector.detect.return_value = (None, np.array([low, high]))
        models._recognizer.feature.return_value = np.ones((1, 128))
        photo = np.zeros((100, 200, 3), np.uint8)
        faces = models.detect(photo)
        models._detector.setInputSize.assert_called_once_with((200, 100))
        np.testing.assert_array_equal(models._recognizer.alignCrop.call_args_list[0].args[1], high)
        self.assertEqual(faces[0].rectangle, (5, 10, 20, 20))
        self.assertAlmostEqual(float(np.linalg.norm(faces[0].vector)), 1.0, places=6)

    def test_bad_cached_model_never_downloads_or_loads(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'face_detection_yunet_2023mar.onnx').write_bytes(b'bad')
            with patch('askai.core.component.faces.models.urlopen') as download, self.assertRaises(ValueError):
                model_path(root, 'yunet')
            download.assert_not_called()

    def test_bad_download_is_not_installed(self):
        with TemporaryDirectory() as directory:
            response = Mock()
            response.read.side_effect = [b'bad', b'']
            context = Mock()
            context.__enter__ = Mock(return_value=response)
            context.__exit__ = Mock(return_value=False)
            with patch('askai.core.component.faces.models.urlopen', return_value=context), self.assertRaises(ValueError):
                model_path(Path(directory), 'yunet')
            self.assertEqual(list(Path(directory).iterdir()), [])
