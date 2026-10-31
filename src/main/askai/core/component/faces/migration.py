"""One-time read-only import of legacy Chroma metadata, recomputing every face."""
import json
import logging
from pathlib import Path
import sqlite3

import cv2
from askai.core.component.faces.index import FaceRecord

MIGRATION_KEY = 'chroma-image-store-to-sface-v1'


def old_faces(database: Path) -> list[dict]:
    if not database.exists():
        return []
    db = sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        rows = db.execute('''
            SELECT e.embedding_id, m.key, m.string_value FROM embeddings e
            JOIN segments s ON s.id=e.segment_id JOIN collections c ON c.id=s.collection
            JOIN embedding_metadata m ON m.id=e.id WHERE c.name=?
        ''', ('image_store',)).fetchall()
    finally:
        db.close()
    records = {}
    for image_id, key, value in rows:
        records.setdefault(image_id, {'id': image_id})[key] = value
    return [record for record in records.values() if record.get('img_category') == 'faces']


def migrate(database: Path, index, models, rebuild=False) -> dict:
    if not rebuild and (previous := index.migration_report(MIGRATION_KEY)):
        return json.loads(previous)
    rows = old_faces(database)
    records, skipped = [], []
    for row in rows:
        path = row.get('img_path') or row.get('chroma:uri')
        if not path or not Path(path).is_file():
            skipped.append({'id': row['id'], 'reason': 'missing_image'})
            continue
        image = cv2.imread(path)
        if image is None:
            skipped.append({'id': row['id'], 'reason': 'unreadable_image'})
            continue
        faces = models.detect(image)
        # Existing records represent one crop; never assign its label to several people.
        if len(faces) != 1:
            skipped.append({'id': row['id'], 'reason': 'no_face' if not faces else 'multiple_faces'})
            continue
        records.append(FaceRecord('migrated-' + row['id'], path, row.get('identity_name'),
                                  row.get('img_caption') or '', faces[0].vector))
    report = {'source_faces': len(rows), 'indexed': len(records), 'skipped': skipped}
    failures = {item['id']: item['reason'] for item in skipped}
    pending = [(row['id'], row.get('img_path') or row.get('chroma:uri'), row.get('identity_name'),
                row.get('img_caption') or '', failures[row['id']]) for row in rows if row['id'] in failures]
    index.add(records, (MIGRATION_KEY, json.dumps(report)), pending)
    logging.info("SFace migration: %d indexed, %d pending; original data preserved", len(records), len(pending))
    return report


if __name__ == '__main__':
    import argparse
    from askai.core.support.app_paths import askai_data_dir
    from askai.core.component.faces.models import FaceModels
    from askai.core.component.faces.index import FaceIndex
    parser = argparse.ArgumentParser(description="Recalculate local face vectors without changing original photos.")
    parser.add_argument('--rebuild', action='store_true', help='Reprocess the original collection, including pending faces.')
    args = parser.parse_args()
    root = askai_data_dir()
    report = migrate(root / 'cache/pictures/image_store/chroma.sqlite3',
                     FaceIndex(root / 'identities/sface.sqlite3'),
                     FaceModels(root / 'cache/models/faces'), rebuild=args.rebuild)
    print(json.dumps(report, ensure_ascii=False))
