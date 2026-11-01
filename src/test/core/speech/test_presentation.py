from threading import Event
import unittest
from unittest.mock import patch
from askai.core.speech.presentation import reveal_text


class PresentationTests(unittest.TestCase):
    def test_progress_follows_duration_without_altering_text(self):
        frames = []
        with patch('askai.core.speech.presentation.monotonic', side_effect=[0, 0, .5, 1]), \
             patch.object(Event, 'wait', return_value=False):
            reveal_text('Olá!', 1, Event(), frames.append)
        self.assertEqual(frames, ['', 'Olá!'])

    def test_cancel_stops_progress(self):
        cancelled = Event()
        frames = []
        def update(text):
            frames.append(text)
            cancelled.set()
        reveal_text('answer', 10, cancelled, update)
        self.assertEqual(len(frames), 1)

    def test_alignment_uses_audio_clock_and_complete_words_at_changed_tempo(self):
        from askai.core.speech.timing import PlaybackTiming
        timing = PlaybackTiming(5, tempo=2, alignment={
            'characters': list('Oi mundo'),
            'character_end_times_seconds': [.1, .2, .3, 1, 2, 3, 4, 5],
        })
        frames = []
        cancel = Event()
        def advance(_):
            timing.position += .1
            if timing.position >= .3:
                cancel.set()
            return cancel.is_set()
        with patch.object(cancel, 'wait', side_effect=advance):
            reveal_text('Oi mundo', timing, cancel, frames.append)
        self.assertEqual(frames, ['', 'Oi '])

    def test_missing_alignment_reveals_words_and_keeps_original_markdown(self):
        from askai.core.speech.timing import PlaybackTiming
        timing = PlaybackTiming(2, position=1)
        cancel = Event()
        frames = []
        def advance(_):
            timing.finished.set()
            return False
        with patch.object(cancel, 'wait', side_effect=advance):
            reveal_text('**Olá** mundo!', timing, cancel, frames.append)
        self.assertEqual(frames[-1], '**Olá** mundo!')
        self.assertTrue(all(frame in ('', '**Olá** ', '**Olá** mundo!') for frame in frames))
