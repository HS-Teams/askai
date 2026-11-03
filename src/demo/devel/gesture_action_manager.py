from askai.core.component.multimedia.audio_player import player
from functools import cached_property, lru_cache
from keras.src.utils import to_categorical
from matplotlib import pyplot as plt
from mediapipe.python.solutions import drawing_utils
from mediapipe.python.solutions.drawing_utils import GREEN_COLOR
from mediapipe.python.solutions.face_mesh_connections import FACEMESH_TESSELATION
from mediapipe.python.solutions.hands_connections import HAND_CONNECTIONS
from mediapipe.python.solutions.holistic import Holistic
from mediapipe.python.solutions.pose_connections import POSE_CONNECTIONS
from numpy import ndarray
from os.path import dirname
from pathlib import Path
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.layers import Dense, LSTM
from tensorflow.keras.models import Sequential
from tensorflow.keras.utils import to_categorical
from typing import Any, Sequence, TypeAlias

import cv2
import numpy as np
import os
import random
import threading

DATA_PATH: Path = Path(os.path.join(dirname(__file__), "mp-data"))
if not DATA_PATH.exists():
    DATA_PATH.mkdir(parents=True, exist_ok=True)

LOGS_PATH: Path = Path(os.path.join(dirname(__file__), "logs"))
if not LOGS_PATH.exists():
    LOGS_PATH.mkdir(parents=True, exist_ok=True)

MODEL_PATH: Path = Path(os.path.join(dirname(__file__), "models"))
if not MODEL_PATH.exists():
    MODEL_PATH.mkdir(parents=True, exist_ok=True)

RgbColor: TypeAlias = tuple[int, int, int]

Position: TypeAlias = tuple[float, float]

GREEN: RgbColor = (0, 255, 0)

BLUE: RgbColor = (0, 0, 255)

YELLOW: RgbColor = (0, 255, 255)

TITLE: RgbColor = GREEN

SUB_TITLE: RgbColor = BLUE


class GestureActionManager:
    # Number of sequences of videos
    NUM_VIDEOS = 30

    # Videos are going to be 30 frames in length
    NUM_FRAMES = 30

    # Pose landmarks: 33 * 4 [x, y, z, vis]
    POSE_LM: int = 33 * 4

    # Face landmarks: 468 * 3 [x, y, z]
    FACE_LM: int = 468 * 3

    # Hand landmarks: 21 * 3 [x, y, z]
    HAND_LM: int = 21 * 3

    # Flat number of keypoints provided by the mediapipe landmarks:
    # pose + face + left_hand + right_hand
    NUM_KEYPOINTS = POSE_LM + FACE_LM + (HAND_LM * 2)

    @staticmethod
    def setup_folder(action: str, sequence_num: int) -> None:
        action_path: str = os.path.join(DATA_PATH, action)
        os.makedirs(os.path.join(action_path, str(sequence_num)), exist_ok=True)

    @staticmethod
    def mediapipe_detection(cv2_frame, model):
        image = cv2.cvtColor(cv2_frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = model.process(image)  # Detect
        image.flags.writeable = True
        image = cv2.cvtColor(cv2_frame, cv2.COLOR_RGB2BGR)  # convert to BGR
        return image, results

    @staticmethod
    def draw_landmarks(image, results) -> None:
        drawing_utils.draw_landmarks(image, results.face_landmarks, FACEMESH_TESSELATION)  # Draw face connections
        drawing_utils.draw_landmarks(image, results.pose_landmarks, POSE_CONNECTIONS)  # Draw pose connections
        drawing_utils.draw_landmarks(image, results.left_hand_landmarks, HAND_CONNECTIONS)  # Draw left hand connections
        drawing_utils.draw_landmarks(
            image, results.right_hand_landmarks, HAND_CONNECTIONS
        )  # Draw right hand connections

    @staticmethod
    def draw_styled_landmarks(image, results) -> None:
        # Draw face connections
        drawing_utils.draw_landmarks(
            image,
            results.face_landmarks,
            FACEMESH_TESSELATION,
            drawing_utils.DrawingSpec(color=(80, 110, 10), thickness=1, circle_radius=1),
            drawing_utils.DrawingSpec(color=(80, 256, 121), thickness=1, circle_radius=1),
        )
        # Draw pose connections
        drawing_utils.draw_landmarks(
            image,
            results.pose_landmarks,
            POSE_CONNECTIONS,
            drawing_utils.DrawingSpec(color=(80, 22, 10), thickness=2, circle_radius=4),
            drawing_utils.DrawingSpec(color=(80, 44, 121), thickness=2, circle_radius=2),
        )
        # Draw left hand connections
        drawing_utils.draw_landmarks(
            image,
            results.left_hand_landmarks,
            HAND_CONNECTIONS,
            drawing_utils.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
            drawing_utils.DrawingSpec(color=(121, 44, 250), thickness=2, circle_radius=2),
        )
        # Draw right hand connections
        drawing_utils.draw_landmarks(
            image,
            results.right_hand_landmarks,
            HAND_CONNECTIONS,
            drawing_utils.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=4),
            drawing_utils.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2),
        )

    @classmethod
    def extract_keypoints(cls, results) -> ndarray:
        pose_lm = results.pose_landmarks
        face_lm = results.face_landmarks
        lh_lm = results.left_hand_landmarks
        rh_lm = results.right_hand_landmarks

        pose = (
            np.array([[res.x, res.y, res.z, res.visibility] for res in pose_lm.landmark]).flatten()
            if pose_lm
            else np.zeros(cls.POSE_LM)
        )
        face = (
            np.array([[res.x, res.y, res.z] for res in face_lm.landmark]).flatten()
            if face_lm
            else np.zeros(cls.FACE_LM)
        )
        lh = np.array([[res.x, res.y, res.z] for res in lh_lm.landmark]).flatten() if lh_lm else np.zeros(cls.HAND_LM)
        rh = np.array([[res.x, res.y, res.z] for res in rh_lm.landmark]).flatten() if rh_lm else np.zeros(cls.HAND_LM)

        return np.concatenate([pose, face, lh, rh])

    @staticmethod
    def display(
        image: cv2.UMat,
        text: str,
        pos: Sequence[int],
        color: Sequence[float] = GREEN_COLOR,
        font_face: int = cv2.FONT_HERSHEY_SIMPLEX,
        font_scale: float = 1,
        thickness: int = 2,
        line_type: int = cv2.LINE_AA,
    ) -> None:
        cv2.putText(image, text, pos, font_face, font_scale, color, thickness, line_type)

    def __init__(self):
        self._actions = np.array(
            [
                # 'maximize', 'minimize', 'grab', 'click',  'pointer', 'next', 'previous', 'dispose'
                "maximize",
                "grab",
            ]
        )
        self._tb_callback = TensorBoard(log_dir=LOGS_PATH)

    @property
    def actions(self) -> ndarray:
        return self._actions

    @cached_property
    def label_map(self) -> dict[tuple[int, Any], int]:
        return {label: num for num, label in enumerate(self._actions)}

    def capture_landmarks(self, start_at: str = "maximize", end_at: str = "dispose") -> None:
        cap = cv2.VideoCapture(0)
        with Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
            start_index = np.where(self.actions == start_at)[0][0]
            end_index = np.where(self.actions == end_at)[0][0]
            for action in self.actions[start_index : end_index + 1]:
                for video_num in range(self.NUM_VIDEOS):
                    for frame_num in range(self.NUM_FRAMES):
                        self.setup_folder(action, video_num)
                        ret, frame = cap.read()
                        image, results = self.mediapipe_detection(frame, holistic)
                        self.draw_styled_landmarks(image, results)

                        if frame_num == 0:
                            threading.Thread(target=player.play_sfx, args=("ui/beep-new-1s",)).start()
                            self.display(image, "STARTING COLLECTION", (120, 120), TITLE)
                            self.display(
                                image, f'Collecting frames for "{action}" Video: # {video_num}', (120, 60), SUB_TITLE
                            )
                            cv2.imshow("OpenCV Feed", image)
                            cv2.waitKey(500)
                        else:
                            self.display(
                                image, f'Collecting frames for "{action}" Video: # {video_num}', (120, 60), SUB_TITLE
                            )
                            cv2.imshow("OpenCV Feed", image)

                        # Extract and save keypoints
                        keypoints = self.extract_keypoints(results)
                        npy_path = os.path.join(DATA_PATH, action, str(video_num), str(frame_num))
                        np.save(npy_path, keypoints)

                        if cv2.waitKey(10) & 0xFF == ord("q"):
                            break

            cap.release()
            cv2.destroyAllWindows()

    def create_sequences_and_labels(self):
        sequences: list = []
        labels: list = []
        for action in self.actions:
            for video_num in np.array(os.listdir(os.path.join(DATA_PATH, action))).astype(int):
                window = []
                for frame_num in range(self.NUM_FRAMES):
                    res = np.load(os.path.join(DATA_PATH, action, str(video_num), f"{frame_num}.npy"))
                    window.append(res)
                sequences.append(window)
                labels.append(self.label_map[action])
        return sequences, labels

    def demo_media_pipe(self):
        cap = cv2.VideoCapture(0)
        with Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
            while cap.isOpened():
                ret, frame = cap.read()
                image, results = self.mediapipe_detection(frame, holistic)
                self.draw_styled_landmarks(image, results)
                keypoints = self.extract_keypoints(results)
                self.display(image, f"Keypoints: {keypoints.shape} ", (120, 60), SUB_TITLE)
                cv2.imshow("OpenCV Feed", image)
                if cv2.waitKey(10) & 0xFF == ord("q"):
                    break
        cap.release()
        cv2.destroyAllWindows()

    def train_model(self, epochs: int = 1000, load: bool = False) -> Sequential:
        print("Training model...")
        sequences, labels = self.create_sequences_and_labels()
        x_arr = np.array(sequences)
        y_arr = to_categorical(labels).astype(int)
        x_train, x_test, y_train, y_test = train_test_split(x_arr, y_arr, test_size=0.05)
        model_path: str = os.path.join(MODEL_PATH, f"taius-{'-'.join(self.actions)}-gestures.h5")
        model = Sequential()
        model.add(LSTM(64, return_sequences=True, activation="relu", input_shape=(self.NUM_FRAMES, self.NUM_KEYPOINTS)))
        model.add(LSTM(128, return_sequences=True, activation="relu"))
        model.add(LSTM(64, return_sequences=False, activation="relu"))
        model.add(Dense(64, activation="relu"))
        model.add(Dense(32, activation="relu"))
        model.add(Dense(self.actions.shape[0], activation="softmax"))
        if not load:
            model.compile(optimizer="Adam", loss="categorical_crossentropy", metrics=["categorical_accuracy"])
            model.fit(x_train, y_train, epochs=epochs, callbacks=[self._tb_callback])
            model.save(model_path)
        else:
            model.load_weights(model_path)
        model.summary()
        print("Model is READY!")
        return model

    @lru_cache
    def rrgb(self, _: int) -> tuple[int, ...]:
        return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)

    def prob_vis(self, results, input_frame) -> Any:
        colors = [self.rrgb(n) for n in range(len(self.actions))]
        output_frame = input_frame.copy()
        for num, prob in enumerate(results):
            self.display(output_frame, str(self.actions[num]), (0, 85 + num * 40), (255, 255, 255))
            if prob >= 0.95:
                print("Action:", str(self.actions[num]))
            cv2.rectangle(output_frame, (0, 60 + num * 40), (int(prob * 100), 90 + num * 40), colors[num], -1)

        return output_frame

    def predict(self, model: Sequential) -> None:
        sequence = []
        actions = []
        predictions = []
        threshold = 0.5
        cap = cv2.VideoCapture(0)

        with Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
            while cap.isOpened():
                ret, frame = cap.read()
                image, results = self.mediapipe_detection(frame, holistic)
                self.draw_styled_landmarks(image, results)

                keypoints = self.extract_keypoints(results)
                sequence.append(keypoints)
                sequence = sequence[-self.NUM_FRAMES :]  # Get the latest sequence.

                if len(sequence) == self.NUM_FRAMES:  # Number of frames to be able to predict.
                    results = model.predict(np.expand_dims(sequence, axis=0))[0]
                    predictions.append(np.argmax(results))  # contains 1 for the detected action: [0, 1, 0] -> minimize
                    if np.unique(predictions[-10:])[0] == np.argmax(results):
                        if results[np.argmax(results)] > threshold:
                            if len(actions) > 0:
                                if self.actions[np.argmax(results)] != actions[-1]:
                                    actions.append(self.actions[np.argmax(results)])
                            else:
                                actions.append(self.actions[np.argmax(results)])
                    if len(actions) > 5:
                        actions = actions[-5:]

                    # Viz probabilities
                    image = self.prob_vis(results, image)

                cv2.rectangle(image, (0, 0), (640, 40), (245, 117, 16), -1)
                self.display(image, " ".join(actions), (3, 30), (255, 255, 255))
                cv2.imshow("OpenCV Feed", image)

                if cv2.waitKey(10) & 0xFF == ord("q"):
                    break

            cap.release()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    gm: GestureActionManager = GestureActionManager()
    # gm.demo_media_pipe()
    # gm.capture_landmarks(start_at='dispose', end_at='dispose')
    gm.predict(gm.train_model(200))
    # gm.predict(gm.train_model(load=True))
