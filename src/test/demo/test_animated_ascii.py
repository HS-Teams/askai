import importlib.util
import io
from pathlib import Path
from threading import Event
import unittest
from unittest.mock import Mock, patch
from PIL import Image
import numpy as np

spec = importlib.util.spec_from_file_location('animated_ascii', Path(__file__).parents[2] / 'demo/devel/animated_ascii.py')
ascii_video = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ascii_video)


class AnimatedAsciiTests(unittest.TestCase):
    def test_reverse_changes_brightness_mapping(self):
        black = Image.new('L', (4, 4), 0)
        self.assertEqual(ascii_video.frame_to_ascii(black, 4, ' .#', False), '    ')
        self.assertEqual(ascii_video.frame_to_ascii(black, 4, ' .#', True), '####')

    def test_portrait_and_tiny_images_fit_both_dimensions(self):
        for shape in ((10, 1000), (1000, 10), (1, 1)):
            image = Image.new('L', shape)
            lines = ascii_video.frame_to_ascii(image, 80, height=12).splitlines()
            self.assertLessEqual(len(lines), 12)
            self.assertTrue(all(0 < len(line) <= 80 for line in lines))

    def test_frame_is_written_once_without_overflow(self):
        output = Mock()
        ascii_video.print_ascii_image('abcdef\n123456\nthird\nfourth', output, (5, 3))
        output.write.assert_called_once()
        text = output.write.call_args.args[0]
        self.assertNotIn('third', text)
        self.assertIn('abcd', text)
        self.assertNotIn('abcde', text)
        output.flush.assert_called_once()

    def test_terminal_restored_after_exception(self):
        output = io.StringIO()
        with patch.object(ascii_video.signal, 'signal', return_value='previous') as signal:
            with self.assertRaisesRegex(RuntimeError, 'failed'):
                with ascii_video.terminal_screen(output, Event()):
                    raise RuntimeError('failed')
        self.assertTrue(output.getvalue().endswith('\x1b[?25h\x1b[?1049l'))
        self.assertEqual(signal.call_count, 4)

    def test_late_frames_are_skipped_without_being_rendered(self):
        capture = Mock()
        position = [0]
        def get(prop):
            return 10 if prop == ascii_video.cv2.CAP_PROP_FPS else position[0]
        def grab():
            position[0] += 1
            return True
        capture.get.side_effect = get
        capture.grab.side_effect = grab
        capture.read.side_effect = [(True, np.zeros((4, 4, 3), dtype=np.uint8)), (False, None)]
        with patch.object(ascii_video, 'print_ascii_image') as render:
            ascii_video.render_video(capture, 10, 10, Event(), Mock(side_effect=[1., 1.2]))
        self.assertGreaterEqual(capture.grab.call_count, 10)
        render.assert_called_once()

    def test_invalid_configuration_is_rejected(self):
        for width, fps in ((0, 10), (10, 0), (10, float('nan'))):
            with self.assertRaises(ValueError):
                ascii_video.play('unused.mp4', width, fps=fps)
