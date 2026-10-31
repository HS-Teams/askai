"""Local face preparation and enrollment, independent of input and presentation."""
from dataclasses import dataclass
import json
from pathlib import Path
import shutil
from uuid import uuid4

import cv2
import numpy as np
from askai.core.component.faces.index import FaceRecord
from askai.core.component.faces.selections import FaceAction, FaceSelection, identity_name, identity_key

@dataclass(frozen=True)
class EnrollmentFace:
    label: int
    path: Path
    caption: str
    vector: np.ndarray
    source_id: str | None = None
    current_name: str | None = None


@dataclass(frozen=True)
class EnrollmentPhoto:
    preview: Path
    faces: list[EnrollmentFace]


class IdentityEnrollment:
    def __init__(self, models, index, face_directory: Path, captioner=None):
        self._models = models
        self._captioner = captioner
        self._index = index
        self._face_directory = face_directory

    def prepare(self, source: str, workspace: Path) -> EnrollmentPhoto:
        """Number YuNet faces, align with SFace and optionally caption the local crops."""
        photo = cv2.imread(source)
        if photo is None:
            raise ValueError(f"Cannot read image: {source}")
        detected = self._models.detect(photo)
        annotated = photo.copy()
        batch = uuid4().hex
        faces = []
        for label, face in enumerate(detected, 1):
            target = workspace / f"{batch}-face-{label}.png"
            self._save(target, face.aligned)
            caption = json.loads(self._captioner(str(target)))["env_description"] if self._captioner else ""
            if not isinstance(caption, str):
                raise ValueError("The local captioner returned an empty description")
            faces.append(EnrollmentFace(label, target, caption, face.vector))
            self._label(annotated, label, face.rectangle)
        preview = workspace / f"{batch}-labels.jpg"
        if faces:
            self._save(preview, annotated)
        return EnrollmentPhoto(preview, faces)

    def identities(self) -> list[dict]:
        return self._index.identities()

    def review(self, workspace: Path) -> EnrollmentPhoto:
        """Build a numbered contact sheet of existing samples, without recapturing."""
        records = self._index.records()
        faces = []
        tile_size, columns = 180, 4
        sheet = np.full((max(1, (len(records) + columns - 1) // columns) * tile_size,
                         columns * tile_size, 3), 245, dtype=np.uint8)
        for label, record in enumerate(records, 1):
            photo = cv2.imread(record.path)
            if photo is None:
                raise ValueError(f'Cannot read registered face: {record.path}')
            height, width = photo.shape[:2]
            factor = min((tile_size - 20) / width, (tile_size - 40) / height)
            thumbnail = cv2.resize(photo, (max(1, round(width * factor)), max(1, round(height * factor))))
            x, y = ((label - 1) % columns) * tile_size, ((label - 1) // columns) * tile_size
            sheet[y + 30:y + 30 + thumbnail.shape[0], x + 10:x + 10 + thumbnail.shape[1]] = thumbnail
            cv2.putText(sheet, str(label), (x + 10, y + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (25, 25, 25), 2)
            faces.append(EnrollmentFace(label, Path(record.path), record.caption, record.vector,
                                        record.id, record.name))
        preview = workspace / 'registered-faces.jpg'
        if faces:
            self._save(preview, sheet)
        return EnrollmentPhoto(preview, faces)

    def plan(self, selections: list[FaceSelection]) -> list[FaceSelection]:
        """Resolve only human choices; recognition never chooses a target identity."""
        existing = {identity_key(item['name']): item['name'] for item in self.identities()}
        created = {}
        for choice in selections:
            if choice.action == FaceAction.NEW:
                name = identity_name(choice.name)
                if not name:
                    raise ValueError('A name is required for a new identity')
                key = identity_key(name)
                if key in existing:
                    raise ValueError(f'Identity already exists: {name}. Choose Merge or Replace.')
                created.setdefault(key, name)
        targets = existing | created
        planned = []
        for choice in selections:
            if choice.action == FaceAction.SKIP:
                continue
            action = FaceAction(choice.action)
            key = identity_key(choice.name)
            if not key or key not in targets:
                raise ValueError('Choose an existing identity for Merge or Replace')
            if action == FaceAction.REPLACE and key not in existing:
                raise ValueError('Replace requires an existing identity')
            planned.append(FaceSelection(choice.face, action, targets[key]))
        return planned

    def save(self, selections: list[FaceSelection]) -> list[dict]:
        """Apply confirmed grouping choices atomically; preserve all original images."""
        planned = self.plan(selections)
        if not planned:
            return []
        self._face_directory.mkdir(parents=True, exist_ok=True)
        records, targets = [], []
        try:
            for choice in planned:
                face = choice.face
                image_id = face.source_id or uuid4().hex
                target = face.path
                if not face.source_id:
                    target = self._face_directory / f'{image_id}-FACE.png'
                    targets.append(target)
                    shutil.copyfile(face.path, target)
                records.append(FaceRecord(image_id, str(target), choice.name, face.caption, face.vector))
            self._index.apply_samples(records, {choice.name for choice in planned if choice.action == FaceAction.REPLACE})
        except Exception:
            for target in targets:
                target.unlink(missing_ok=True)
            raise
        totals = {identity_key(item['name']): item['samples'] for item in self.identities()}
        grouped = {}
        for choice in planned:
            entry = grouped.setdefault(choice.name, {'name': choice.name, 'selected_samples': 0, 'actions': []})
            entry['selected_samples'] += 1
            if choice.action.value not in entry['actions']:
                entry['actions'].append(choice.action.value)
            entry['total_samples'] = totals.get(identity_key(choice.name), 0)
        return list(grouped.values())

    @staticmethod
    def _save(target, photo):
        if not cv2.imwrite(str(target), photo):
            raise OSError(f"Could not save image: {target}")

    @staticmethod
    def _label(image, label, region):
        x, y, width, height = region
        color = (0, 220, 255)
        thickness = max(2, round(min(image.shape[:2]) / 400))
        scale = max(0.6, min(image.shape[:2]) / 900)
        text = str(label)
        (text_width, text_height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
        left = min(x, max(0, image.shape[1] - text_width - 12))
        top = max(0, y - text_height - baseline - 12)
        cv2.rectangle(image, (x, y), (x + width, y + height), color, thickness)
        cv2.rectangle(image, (left, top), (left + text_width + 12, top + text_height + baseline + 12), color, -1)
        cv2.putText(image, text, (left + 6, top + text_height + 6), cv2.FONT_HERSHEY_SIMPLEX,
                    scale, (25, 25, 25), thickness, cv2.LINE_AA)
