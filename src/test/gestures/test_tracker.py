import unittest
from types import SimpleNamespace
from askai.gestures.tracker import right_hand_points


def result_for(*labels):
    return SimpleNamespace(
        hand_landmarks=[[SimpleNamespace(x=i / 10, y=.3)] * 21 for i in range(len(labels))],
        hand_world_landmarks=[[SimpleNamespace(x=i / 100, y=.02, z=-.03)] * 21
                              for i in range(len(labels))],
        handedness=[[SimpleNamespace(category_name=label, score=.95)] for label in labels],
    )


class RightHandTests(unittest.TestCase):
    def test_right_hand_selected_regardless_of_detection_order(self):
        for labels in [('Left', 'Right'), ('Right', 'Left')]:
            result = result_for(*labels)
            index = labels.index('Right')
            self.assertEqual(right_hand_points(result),
                             ([(index / 10, .3)] * 21, [(index / 100, .02, -.03)] * 21))

    def test_left_hand_never_takes_control(self):
        self.assertEqual(right_hand_points(result_for('Left')), ([], []))
        self.assertEqual(right_hand_points(result_for()), ([], []))

    def test_missing_classification_does_not_control_pointer(self):
        result = result_for('Right')
        result.handedness = [[]]
        self.assertEqual(right_hand_points(result), ([], []))

    def test_missing_world_landmarks_cannot_be_used_as_a_flat_pinch(self):
        result = result_for('Right')
        result.hand_world_landmarks = []
        self.assertEqual(right_hand_points(result), ([], []))


class BodyTrackerTests(unittest.TestCase):
    def test_hand_and_body_use_same_frame_and_increasing_timestamps(self):
        from unittest.mock import Mock, patch
        import numpy as np
        from askai.gestures.tracker import HandTracker
        from test_waist import body
        mp, cv = Mock(), Mock()
        vision = mp.tasks.vision
        hand = vision.HandLandmarker.create_from_options.return_value
        pose = vision.PoseLandmarker.create_from_options.return_value
        result = result_for('Right')
        result.hand_landmarks[0][0].x = .55
        result.hand_landmarks[0][0].y = .4
        hand.detect_for_video.return_value = result
        pose.detect_for_video.return_value = body()
        with patch.dict('sys.modules', mediapipe=mp, cv2=cv), patch(
                'askai.gestures.tracker.monotonic_ns', return_value=10_000_000):
            tracker = HandTracker('hand.task', 'pose.task')
            for _ in range(2):
                points, world, waist = tracker.detect(np.zeros((100, 100, 3)))
                self.assertEqual(len(points), 21)
                self.assertEqual(len(world), 21)
                self.assertIsNotNone(waist)
            tracker.close()
        self.assertEqual(hand.detect_for_video.call_args_list, pose.detect_for_video.call_args_list)
        self.assertEqual([c.args[1] for c in pose.detect_for_video.call_args_list], [10, 11])
        hand.close.assert_called_once()
        pose.close.assert_called_once()

    def test_failed_body_initialization_closes_hand_detector(self):
        from unittest.mock import Mock, patch
        from askai.gestures.tracker import HandTracker
        mp = Mock()
        mp.tasks.vision.PoseLandmarker.create_from_options.side_effect = RuntimeError('Invalid model')
        with patch.dict('sys.modules', mediapipe=mp), self.assertRaisesRegex(RuntimeError, 'Invalid model'):
            HandTracker('hand.task', 'pose.task')
        mp.tasks.vision.HandLandmarker.create_from_options.return_value.close.assert_called_once()

    def test_body_model_is_downloaded_once_and_kept_separate_from_hand_model(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import Mock, patch
        from askai.gestures.tracker import pose_model_path, POSE_MODEL_URL
        requests = Mock()
        response = requests.get.return_value.__enter__ = Mock(return_value=Mock())
        requests.get.return_value.__exit__ = Mock(return_value=False)
        response.return_value.iter_content.return_value = [b'pose model']
        with TemporaryDirectory() as storage, patch.dict('sys.modules', requests=requests):
            path = pose_model_path(storage)
            self.assertEqual(path, Path(storage) / 'models/gestures/pose_landmarker_lite.task')
            self.assertEqual(path.read_bytes(), b'pose model')
            self.assertEqual(pose_model_path(storage), path)
            requests.get.assert_called_once_with(POSE_MODEL_URL, stream=True, timeout=(5, 60))

    def test_empty_body_model_download_leaves_no_cached_file(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import MagicMock, patch
        from askai.gestures.tracker import pose_model_path
        requests = MagicMock()
        requests.get.return_value.__enter__.return_value.iter_content.return_value = []
        with TemporaryDirectory() as storage, patch.dict('sys.modules', requests=requests):
            with self.assertRaisesRegex(RuntimeError, 'Empty gesture model'):
                pose_model_path(storage)
            self.assertEqual(list((Path(storage) / 'models/gestures').iterdir()), [])
