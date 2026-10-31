import ast
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import os
import re
import unittest
from unittest.mock import Mock


def cache_service(root, enabled):
    source = Path(__file__).parents[3] / 'main/askai/core/component/cache_service.py'
    tree = ast.parse(source.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'CacheService')
    cls.keywords = []
    cls.body = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in
                ('save_input_history','read_input_history','save_context','read_context','save_memory','read_memory','audio_file_path')]
    tree.body = [ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), cls]
    scope = dict(configs=SimpleNamespace(is_keep_context=enabled, is_cache=enabled),
                 KeyboardInput=Mock(), Charset=SimpleNamespace(UTF_8=SimpleNamespace(val='utf-8')),
                 os=os, re=re, AUDIO_DIR=root, hash_text=lambda text: 'hash',
                 file_is_not_empty=lambda path: Path(path).exists())
    for key in ('ASKAI_INPUT_HISTORY_FILE','ASKAI_CONTEXT_FILE','ASKAI_MEMORY_FILE'):
        scope[key] = root / key
        scope[key].write_text('existing')
    exec(compile(ast.fix_missing_locations(tree), str(source), 'exec'), scope)
    service = scope['CacheService']()
    service._private_inputs = set()
    return service, scope


class HistoryStorageTests(unittest.TestCase):
    def test_off_skips_history_reads_and_writes(self):
        with TemporaryDirectory() as directory:
            cache, scope = cache_service(Path(directory), False)
            cache.save_input_history(['private question'])
            cache.save_context(['human: private question'])
            cache.save_memory([SimpleNamespace(role='user', content='private question', recordable=False)])
            self.assertEqual(cache.read_input_history(), [])
            self.assertEqual(cache.read_context(), [])
            self.assertEqual(cache.read_memory(), [])
            for path in Path(directory).iterdir():
                self.assertEqual(path.read_text(), 'existing')
            scope['configs'].is_keep_context = True
            cache.save_input_history(['private question', 'public question'])
            self.assertEqual(cache.read_input_history(), ['existing', 'public question'])
            cache.save_memory([SimpleNamespace(role='user',content='private',recordable=False),
                               SimpleNamespace(role='user',content='public',recordable=True)])
            self.assertNotIn('private', scope['ASKAI_MEMORY_FILE'].read_text())

    def test_audio_off_never_reuses_existing_cache(self):
        with TemporaryDirectory() as directory:
            cache, scope = cache_service(Path(directory), True)
            filename, _ = cache.audio_file_path('hello', 'voice', 'wav')
            Path(filename).write_bytes(b'cached')
            self.assertTrue(cache.audio_file_path('hello', 'voice', 'wav')[1])
            scope['configs'].is_cache = False
            temporary, hit = cache.audio_file_path('hello', 'voice', 'wav')
            self.assertFalse(hit)
            self.assertNotEqual(temporary, filename)
            self.assertEqual(Path(filename).read_bytes(), b'cached')
