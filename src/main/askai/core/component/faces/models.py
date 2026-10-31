"""Verified OpenCV models, loaded once and shared by local face operations."""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from urllib.request import urlopen

import cv2
import numpy as np

MODEL_VERSION = 'sface-2021dec'
VECTOR_SIZE = 128
DEFAULT_THRESHOLD = 0.363  # OpenCV's published SFace cosine threshold for LFW.
MODEL_FILES = {
    'yunet': ('face_detection_yunet', 'face_detection_yunet_2023mar.onnx',
              '8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4'),
    'sface': ('face_recognition_sface', 'face_recognition_sface_2021dec.onnx',
              '0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79'),
}


def model_path(directory: Path, kind: str) -> Path:
    folder, filename, digest = MODEL_FILES[kind]
    target = directory / filename
    if target.exists():
        if sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Invalid model checksum: {target}')
        return target
    directory.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(dir=directory, delete=False) as output:
            temporary = Path(output.name)
            url = f'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/{folder}/{filename}'
            with urlopen(url, timeout=60) as response:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
        if sha256(temporary.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Invalid downloaded model checksum: {filename}')
        temporary.replace(target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target


def normalized(vector) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.float32).reshape(-1)
    if vector.size != VECTOR_SIZE or not np.isfinite(vector).all():
        raise ValueError('Invalid SFace embedding')
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError('Empty SFace embedding')
    return vector / norm


@dataclass(frozen=True)
class DetectedFace:
    rectangle: tuple[int, int, int, int]
    aligned: np.ndarray
    vector: np.ndarray


class FaceModels:
    def __init__(self, directory: Path):
        self._detector = cv2.FaceDetectorYN.create(str(model_path(directory, 'yunet')), '', (320, 320))
        self._recognizer = cv2.FaceRecognizerSF.create(str(model_path(directory, 'sface')), '')
        self._lock = Lock()

    def detect(self, photo) -> list[DetectedFace]:
        if photo is None or photo.size == 0:
            raise ValueError('Cannot read face image')
        height, width = photo.shape[:2]
        with self._lock:
            self._detector.setInputSize((width, height))
            _, faces = self._detector.detect(photo)
            if faces is None:
                return []
            result = []
            for face in sorted(faces, key=lambda value: (value[1], value[0])):
                aligned = self._recognizer.alignCrop(photo, face)
                vector = normalized(self._recognizer.feature(aligned))
                x, y, w, h = face[:4]
                left, top = max(0, int(x)), max(0, int(y))
                right, bottom = min(width, int(x + w)), min(height, int(y + h))
                result.append(DetectedFace((left, top, right - left, bottom - top), aligned, vector))
            return result
