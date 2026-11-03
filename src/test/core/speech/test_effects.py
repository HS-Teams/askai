from io import StringIO
from pathlib import Path
from threading import Event
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, MagicMock, patch
from askai.core.speech import effects
from askai.core.speech.playback import play_speech


class EffectChannelTests(unittest.TestCase):
    def setUp(self):
        for name, value in (('_muted', False), ('_players', set())):
            patcher = patch.object(effects, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_muting_stops_only_sound_effect_players(self):
        effect = Mock(poll=Mock(return_value=None))
        speech = Mock(poll=Mock(return_value=None))
        effects._players.add(effect)
        effects.set_muted(True)
        effect.terminate.assert_called_once()
        speech.terminate.assert_not_called()
        with patch.object(effects.subprocess, 'Popen') as popen:
            self.assertTrue(effects.play('/tmp/effect.mp3'))
        popen.assert_not_called()

    def test_speech_can_play_while_effects_are_muted(self):
        effects.set_muted(True)
        process = MagicMock(returncode=0)
        process.__enter__.return_value = process
        process.poll.return_value = 0
        with patch('askai.core.speech.playback.subprocess.Popen', return_value=process) as popen:
            play_speech(Path('/tmp/speech.wav'), 1, Event())
        popen.assert_called_once()
        process.terminate.assert_not_called()

    def test_restart_reads_saved_effect_setting_without_consulting_speak(self):
        effects._muted = None
        settings = Mock()
        for muted in (True, False):
            settings.get_bool.return_value = muted
            with patch.dict('sys.modules', {'askai.core.askai_settings': NS(settings=settings)}):
                self.assertEqual(effects.is_muted(), muted)
        self.assertTrue(all(call.args == ('askai.sfx.muted',) for call in settings.get_bool.call_args_list))

    def test_unmute_restores_effects_and_reaps_owned_process(self):
        effects.set_muted(True)
        effects.set_muted(False)
        process = Mock(wait=Mock(return_value=0), poll=Mock(return_value=0))
        with patch.object(effects.subprocess, 'Popen', return_value=process) as popen:
            self.assertTrue(effects.play('/tmp/an effect.mp3', timeout=5))
        self.assertEqual(popen.call_args.args[0][-1], '/tmp/an effect.mp3')
        self.assertNotIn('shell', popen.call_args.kwargs)
        self.assertFalse(effects._players)

    def test_running_worker_mute_controls_do_not_change_ptt_pause(self):
        from askai.gestures.worker import read_controls
        paused = Event()
        paused.set()
        read_controls(StringIO('mute_sfx\n'), paused)
        self.assertTrue(effects.is_muted())
        self.assertTrue(paused.is_set())
        read_controls(StringIO('unmute_sfx\n'), paused)
        self.assertFalse(effects.is_muted())
        self.assertTrue(paused.is_set())

    def test_muted_gesture_effect_does_not_start_audio_thread(self):
        from askai.gestures import sfx
        effects.set_muted(True)
        with patch.object(sfx, 'Thread') as thread:
            sfx.play_click()
        thread.assert_not_called()
