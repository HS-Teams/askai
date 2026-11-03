"""MediaPipe adapter and local model provisioning; never stores captured frames."""
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import monotonic_ns
from askai.gestures.waist import waist_boundary

MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'
POSE_MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task'


def model_path(storage):
    return _model_path(storage, 'hand_landmarker.task', MODEL_URL)


def pose_model_path(storage):
    return _model_path(storage, 'pose_landmarker_lite.task', POSE_MODEL_URL)


def _model_path(storage, filename, url):
    path = Path(storage) / 'models' / 'gestures' / filename
    if path.is_file() and path.stat().st_size:
        return path
    import requests
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        try:
            with requests.get(url, stream=True, timeout=(5, 60)) as response:
                response.raise_for_status()
                for chunk in response.iter_content(65536):
                    output.write(chunk)
            output.flush()
            if not temporary.stat().st_size:
                raise RuntimeError('Empty gesture model download')
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    return path


class HandTracker:
    def __init__(self, path, pose_path):
        import mediapipe as mp
        self._mp = mp
        vision = mp.tasks.vision
        self._model = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(path)),
            running_mode=vision.RunningMode.VIDEO, num_hands=2,
            min_hand_detection_confidence=.7, min_hand_presence_confidence=.7,
            min_tracking_confidence=.7,
        ))
        try:
            self._pose_model = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(pose_path)),
                running_mode=vision.RunningMode.VIDEO, num_poses=1,
                min_pose_detection_confidence=.7, min_pose_presence_confidence=.7,
                min_tracking_confidence=.7,
            ))
        except BaseException:
            self._model.close()
            raise
        self._timestamp = 0

    def detect(self, frame):
        import cv2
        self._timestamp = max(self._timestamp + 1, monotonic_ns() // 1000000)
        image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB,
                               data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        result = self._model.detect_for_video(image, self._timestamp)
        points, world_points = right_hand_points(result)
        pose = self._pose_model.detect_for_video(image, self._timestamp)
        waist = waist_boundary(pose, points, frame.shape[1] / frame.shape[0])
        return points, world_points, waist

    def close(self):
        try:
            self._model.close()
        finally:
            self._pose_model.close()


def right_hand_points(result):
    """Select the subject's right hand from an unmirrored camera frame."""
    for landmarks, world_landmarks, categories in zip(
            result.hand_landmarks, result.hand_world_landmarks, result.handedness):
        if categories and max(categories, key=lambda category: category.score).category_name == 'Right':
            return ([(point.x, point.y) for point in landmarks],
                    [(point.x, point.y, point.z) for point in world_landmarks])
    return [], []
