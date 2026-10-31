import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from askai.core.engine.llama.llama_speech import LlamaSpeech


class SpeechTests(unittest.TestCase):
    def setUp(self):
        self.config = SimpleNamespace(
            base_url="http://localhost:11434",
            timeout=120,
            tts_model="phonon",
            tts_voice="Grub the Ogre",
            tempo=1,
        )
        self.client = Mock()
        self.client.show.return_value = {"voices": ["Grub the Ogre", "Zoey"]}
        self.speech = LlamaSpeech(self.client, self.config)

    def test_selection_and_override_preserve_preferences(self):
        self.speech.select_voice("Zoey")
        self.assertEqual(self.speech.voice, "Zoey")
        with self.assertRaises(ValueError):
            self.speech.select_voice("missing")

    def test_existing_cache_identity_is_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "audio.wav"
            cache = Mock()
            cache.audio_file_path.side_effect = lambda *args: (
                str(target),
                target.exists(),
            )

            def generate(command, **kwargs):
                self.assertEqual(
                    command, ["ollama", "run", "phonon", "--voice", "Zoey"]
                )
                self.assertEqual(kwargs["input"], b"hello")
                kwargs["stdout"].write(b"RIFF" + b"\x00" * 4 + b"WAVE" + b"data")

            with patch.dict(
                sys.modules,
                {"askai.core.component.cache_service": SimpleNamespace(cache=cache)},
            ), patch("subprocess.run", side_effect=generate) as run:
                for _ in range(2):
                    self.speech.synthesize("hello", voice="Zoey", playback=False)
                run.assert_called_once()
                self.assertEqual(
                    cache.audio_file_path.call_args.args,
                    ("hello", "ollama:http://localhost:11434:phonon:Zoey", "wav"),
                )
                self.assertEqual(self.speech.voice, "Grub the Ogre")

    def test_failed_synthesis_is_not_cached(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "audio.wav"
            with patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(
                    1, "ollama", stderr=b"failed"
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "failed"):
                    self.speech._generate("hello", "Grub the Ogre", target)
            self.assertFalse(target.exists())
