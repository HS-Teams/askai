from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from askai.core.speech.dictation_memory import register, context
from askai.core.support.persistent_memory import PersistentMemory
from askai.core.support.short_term_memory import ShortTermMemory


class DictationMemoryTests(unittest.TestCase):
    def test_history_on_restores_latest_refined_dictation_after_restart(self):
        with TemporaryDirectory() as directory:
            cwd = Path(directory).resolve()
            durable = PersistentMemory(cwd / 'history.sqlite3')
            memory = ShortTermMemory(4)
            for name in ('first', 'last'):
                register(memory, durable, 'codex', cwd, cwd / (name + '.original'),
                         cwd / (name + '.txt'), name + ' refined text')
            restored = context(ShortTermMemory(4), PersistentMemory(durable.path), 'codex', cwd)
            self.assertIn('last.txt', restored)
            self.assertNotIn('first.txt', restored)
            self.assertEqual(durable.latest_dictation('codex', str(cwd))['text'], 'last refined text')
            self.assertEqual(durable.conversations('codex', str(cwd))[-1]['answer'], 'last refined text')
            self.assertEqual(context(memory, durable, 'claude', cwd), '')
            self.assertEqual(context(memory, durable, 'codex', cwd / 'other'), '')

    def test_history_off_is_live_only_and_does_not_resume_old_records(self):
        with TemporaryDirectory() as directory:
            cwd = Path(directory).resolve()
            memory = ShortTermMemory(4)
            register(memory, None, 'codex', cwd, cwd / 'raw', cwd / 'refined', 'text')
            self.assertIn('refined', context(memory, None, 'codex', cwd))
            self.assertFalse(memory.messages[-1].recordable)
            self.assertEqual(list(cwd.iterdir()), [])
            self.assertEqual(context(ShortTermMemory(4), None, 'codex', cwd), '')

    def test_live_private_dictation_takes_precedence_without_becoming_persistent(self):
        with TemporaryDirectory() as directory:
            cwd = Path(directory).resolve()
            durable = PersistentMemory(cwd / 'history.sqlite3')
            memory = ShortTermMemory(4)
            register(memory, durable, 'codex', cwd, cwd / 'old.raw', cwd / 'old.txt', 'old')
            register(memory, None, 'codex', cwd, cwd / 'private.raw', cwd / 'private.txt', 'private')
            self.assertIn('private.txt', context(memory, durable, 'codex', cwd))
            self.assertEqual(durable.latest_dictation('codex', str(cwd))['text'], 'old')
            self.assertIn('old.txt', context(ShortTermMemory(4), durable, 'codex', cwd))
