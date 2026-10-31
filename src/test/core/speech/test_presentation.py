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
        self.assertEqual(frames, ['', 'Ol', 'Olá!'])

    def test_cancel_stops_progress(self):
        cancelled = Event()
        frames = []
        def update(text):
            frames.append(text)
            cancelled.set()
        reveal_text('answer', 10, cancelled, update)
        self.assertEqual(len(frames), 1)
