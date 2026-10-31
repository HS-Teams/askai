import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from askai.core.support.cache_policy import optional_cache, transient_audio_path, release_transient_audio


class CachePolicyTests(unittest.TestCase):
    def test_off_bypasses_reads_and_writes_preserving_existing_entries(self):
        operation = Mock(side_effect=lambda value: object())
        cached = optional_cache()(operation)
        with patch('askai.core.support.cache_policy.cache_enabled', return_value=True):
            original = cached('old')
            self.assertIs(cached('old'), original)
        with patch('askai.core.support.cache_policy.cache_enabled', return_value=False):
            self.assertIsNot(cached('old'), original)
            temporary = cached('new')
            self.assertIsNot(cached('new'), temporary)
        with patch('askai.core.support.cache_policy.cache_enabled', return_value=True):
            self.assertIs(cached('old'), original)
            self.assertIsNot(cached('new'), temporary)
        self.assertEqual(operation.call_count, 5)

    def test_transient_audio_is_unique_and_only_owned_files_are_removed(self):
        first, hit = transient_audio_path('wav')
        second, _ = transient_audio_path('wav')
        self.assertFalse(hit)
        self.assertNotEqual(first, second)
        Path(first).write_bytes(b'audio')
        release_transient_audio(first)
        self.assertFalse(Path(first).exists())
