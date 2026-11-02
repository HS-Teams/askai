import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
from askai.gestures.preview import Pointer


def screen(x, y, width, height):
    return NS(origin=NS(x=x, y=y), size=NS(width=width, height=height))


class MonitorTests(unittest.TestCase):
    def pointer(self, screens):
        pointer = Pointer.__new__(Pointer)
        pointer._screens = screens
        pointer._pressed = False
        pointer._position = None
        return pointer

    def test_crosses_to_monitor_with_negative_coordinates(self):
        pointer = self.pointer([screen(-1920, 0, 1920, 1080), screen(0, 0, 1920, 1080)])
        with patch.dict('sys.modules', Quartz=Mock()):
            pointer.move(.25, .5)
            self.assertLess(pointer._position[0], 0)
            pointer.move(.75, .5)
            self.assertGreater(pointer._position[0], 0)

    def test_vertical_monitor_is_reachable_and_gaps_are_projected(self):
        pointer = self.pointer([screen(0, 0, 1920, 1080), screen(0, -1080, 1280, 1080)])
        with patch.dict('sys.modules', Quartz=Mock()):
            pointer.move(.3, .1)
            self.assertLess(pointer._position[1], 0)
            pointer.move(1., 0.)
            x, y = pointer._position
            self.assertTrue(any(r.origin.x <= x < r.origin.x + r.size.width and
                                r.origin.y <= y < r.origin.y + r.size.height for r in pointer._screens))
