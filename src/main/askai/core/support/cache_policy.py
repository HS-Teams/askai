"""Apply the runtime cache switch without discarding existing cached data."""
from functools import lru_cache, wraps
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from threading import Lock


def cache_enabled():
    from askai.core.askai_configs import configs
    return configs.is_cache


def optional_cache(maxsize=128):
    def decorate(function):
        cached = lru_cache(maxsize=maxsize)(function)
        @wraps(function)
        def invoke(*args, **kwargs):
            return (cached if cache_enabled() else function)(*args, **kwargs)
        invoke.cache_clear = cached.cache_clear
        invoke.cache_info = cached.cache_info
        return invoke
    return decorate


_audio_directory = None
_audio_lock = Lock()


def transient_audio_path(audio_format):
    global _audio_directory
    with _audio_lock:
        if _audio_directory is None:
            _audio_directory = TemporaryDirectory(prefix='askai-audio-')
    return str(Path(_audio_directory.name) / f'{uuid4().hex}.{audio_format}'), False


def release_transient_audio(path):
    if path and _audio_directory is not None and Path(path).parent == Path(_audio_directory.name):
        Path(path).unlink(missing_ok=True)
