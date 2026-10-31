"""Transactional local identity index; SFace vectors never mix with OpenCLIP."""
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sqlite3

import numpy as np
from askai.core.component.faces.models import MODEL_VERSION, normalized
from askai.core.component.faces.selections import identity_key


@dataclass(frozen=True)
class FaceRecord:
    id: str
    path: str
    name: str | None
    caption: str
    vector: np.ndarray


class FaceIndex:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS faces (
                    id TEXT PRIMARY KEY, path TEXT NOT NULL, name TEXT, caption TEXT NOT NULL,
                    model TEXT NOT NULL, vector BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS migrations (source TEXT PRIMARY KEY, report TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS managed_faces (id TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS pending_faces (
                    id TEXT PRIMARY KEY, path TEXT, name TEXT, caption TEXT, reason TEXT NOT NULL
                );
            ''')

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        try:
            with db:
                yield db
        finally:
            db.close()

    def add(self, records: list[FaceRecord], migration: tuple[str, str] | None = None, pending=()):
        rows = [(r.id, r.path, r.name, r.caption, MODEL_VERSION, normalized(r.vector).tobytes()) for r in records]
        with self._connect() as db:
            if migration:
                managed = {row[0] for row in db.execute('SELECT id FROM managed_faces')}
                rows = [row for row in rows if row[0] not in managed]
                db.execute("DELETE FROM faces WHERE id LIKE 'migrated-%' AND id NOT IN (SELECT id FROM managed_faces)")
                db.execute('DELETE FROM pending_faces')
                db.executemany('INSERT INTO pending_faces VALUES (?, ?, ?, ?, ?)', pending)
            db.executemany('INSERT INTO faces VALUES (?, ?, ?, ?, ?, ?)', rows)
            if migration:
                db.execute('INSERT OR REPLACE INTO migrations VALUES (?, ?)', migration)

    def migration_report(self, source: str) -> str | None:
        with self._connect() as db:
            row = db.execute('SELECT report FROM migrations WHERE source=?', (source,)).fetchone()
        return row[0] if row else None

    def records(self) -> list[FaceRecord]:
        with self._connect() as db:
            rows = db.execute('SELECT id,path,name,caption,vector FROM faces WHERE model=?', (MODEL_VERSION,)).fetchall()
        return [FaceRecord(*row[:4], normalized(np.frombuffer(row[4], dtype=np.float32))) for row in rows]

    def identities(self) -> list[dict]:
        grouped = {}
        for record in self.records():
            if record.name:
                key = identity_key(record.name)
                entry = grouped.setdefault(key, {'name': record.name, 'samples': 0})
                entry['samples'] += 1
        return sorted(grouped.values(), key=lambda item: identity_key(item['name']))

    def apply_samples(self, records: list[FaceRecord], replace_names: set[str]):
        """Replace identity samples and reassign selected faces in one transaction."""
        rows = [(r.id, r.path, r.name, r.caption, MODEL_VERSION, normalized(r.vector).tobytes()) for r in records]
        replaced = {identity_key(name) for name in replace_names}
        with self._connect() as db:
            existing = db.execute('SELECT id,name FROM faces').fetchall()
            deleted = [record_id for record_id, name in existing if name and identity_key(name) in replaced]
            managed = set(deleted) | {record.id for record in records}
            db.executemany('INSERT OR IGNORE INTO managed_faces VALUES (?)', [(record_id,) for record_id in managed])
            db.executemany('DELETE FROM faces WHERE id=?', [(record_id,) for record_id in deleted])
            db.executemany('INSERT OR REPLACE INTO faces VALUES (?, ?, ?, ?, ?, ?)', rows)

    def match(self, vectors, threshold: float) -> list[dict]:
        if not np.isfinite(threshold) or not -1 <= threshold <= 1:
            raise ValueError('SFace cosine threshold must be between -1 and 1')
        records = self.records()
        matrix = np.stack([record.vector for record in records]) if records else None
        matches = []
        for label, vector in enumerate(vectors, 1):
            result = {'face': label, 'status': 'unknown', 'name': None}
            if records:
                scores = matrix @ normalized(vector)
                best = int(np.argmax(scores))
                score = float(np.clip(scores[best], -1, 1))
                if score >= threshold:
                    record = records[best]
                    result.update(status='matched' if record.name else 'unlabelled',
                                  name=record.name, similarity=score, caption=record.caption)
            matches.append(result)
        return matches
