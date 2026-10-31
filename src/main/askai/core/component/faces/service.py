"""Lazy process-wide models and the persistent local face index."""
from functools import lru_cache
from askai.core.support.app_paths import askai_data_dir
from askai.core.component.faces.models import FaceModels
from askai.core.component.faces.index import FaceIndex
from askai.core.component.faces.migration import migrate


@lru_cache(maxsize=1)
def face_services():
    root = askai_data_dir()
    models = FaceModels(root / 'cache/models/faces')
    index = FaceIndex(root / 'identities/sface.sqlite3')
    report = migrate(root / 'cache/pictures/image_store/chroma.sqlite3', index, models)
    return models, index, report
