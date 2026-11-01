"""MediaPipe adapter and local model provisioning; never stores captured frames."""
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import monotonic_ns

MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'


def model_path(storage):
    path = Path(storage) / 'models' / 'gestures' / 'hand_landmarker.task'
    if path.is_file() and path.stat().st_size:
        return path
    import requests
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        try:
            with requests.get(MODEL_URL, stream=True, timeout=(5, 60)) as response:
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
    def __init__(self, path):
        import mediapipe as mp
        self._mp = mp
        vision = mp.tasks.vision
        self._model = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(path)),
            running_mode=vision.RunningMode.VIDEO, num_hands=2,
            min_hand_detection_confidence=.7, min_hand_presence_confidence=.7,
            min_tracking_confidence=.7,
        ))
        self._timestamp = 0

    def detect(self, frame):
        import cv2
        self._timestamp = max(self._timestamp + 1, monotonic_ns() // 1000000)
        image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB,
                               data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        result = self._model.detect_for_video(image, self._timestamp)
        return right_hand_points(result)

    def close(self):
        self._model.close()


def right_hand_points(result):
    """Select the subject's right hand from an unmirrored camera frame."""
    for landmarks, categories in zip(result.hand_landmarks, result.handedness):
        if categories and max(categories, key=lambda category: category.score).category_name == 'Right':
            return [(point.x, point.y) for point in landmarks]
    return []
