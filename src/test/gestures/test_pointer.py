import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch, call
import numpy as np
from askai.gestures.controller import GestureState
from askai.gestures.preview import Pointer, Preview


class PointerTests(unittest.TestCase):
    def setUp(self):
        sound = patch('askai.gestures.sfx._play')
        sound.start()
        self.addCleanup(sound.stop)

    def test_scroll_uses_native_wheel_without_repositioning_pointer(self):
        pointer = Pointer.__new__(Pointer)
        pointer._mouse = Mock()
        pointer._position = (-1500, 300)
        quartz = Mock()
        with patch.dict('sys.modules', Quartz=quartz):
            pointer.scroll(1)
            pointer.scroll(-1)
        self.assertEqual(quartz.CGEventCreateScrollWheelEvent.call_args_list,
                         [call(None, quartz.kCGScrollEventUnitLine, 1, 1),
                          call(None, quartz.kCGScrollEventUnitLine, 1, -1)])
        self.assertEqual(quartz.CGEventPost.call_count, 2)
        quartz.CGEventCreateMouseEvent.assert_not_called()
        self.assertEqual(pointer._position, (-1500, 300))
        self.assertEqual(pointer._mouse.mock_calls, [])

    def test_scroll_boundaries_target_focused_application_without_moving_pointer(self):
        pointer = Pointer.__new__(Pointer)
        pointer._position = (-1500, 300)
        quartz, appkit = Mock(), Mock()
        appkit.NSWorkspace.sharedWorkspace.return_value.frontmostApplication.return_value.processIdentifier.return_value = 42
        with patch.dict('sys.modules', Quartz=quartz, AppKit=appkit):
            pointer.scroll_boundary('top')
            pointer.scroll_boundary('bottom')
        self.assertEqual(quartz.CGEventCreateKeyboardEvent.call_args_list,
                         [call(None, 126, True), call(None, 126, False),
                          call(None, 125, True), call(None, 125, False)])
        self.assertEqual(quartz.CGEventSetFlags.call_args_list,
                         [call(quartz.CGEventCreateKeyboardEvent.return_value,
                               quartz.kCGEventFlagMaskCommand)] * 4)
        self.assertEqual(quartz.CGEventPostToPid.call_args_list,
                         [call(42, quartz.CGEventCreateKeyboardEvent.return_value)] * 4)
        quartz.CGEventCreateMouseEvent.assert_not_called()
        self.assertEqual(pointer._position, (-1500, 300))

    def test_drag_events_and_release_are_idempotent(self):
        pointer = Pointer.__new__(Pointer)
        pointer._mouse = Mock()
        pointer._screens = [NS(origin=NS(x=0, y=0), size=NS(width=100, height=100))]
        pointer._pressed = False
        pointer._position = None
        quartz = Mock()
        with patch.dict('sys.modules', Quartz=quartz):
            pointer.press()
            pointer.press()
            pointer.move(.5, .5)
            self.assertEqual(quartz.CGEventCreateMouseEvent.call_args.args[1],
                             quartz.kCGEventLeftMouseDragged)
            pointer.move(.5, .5)
            self.assertEqual(quartz.CGEventPost.call_count, 1)
            pointer.release()
            pointer.release()
        pointer._mouse.mouseDown.assert_called_once()
        self.assertEqual(quartz.CGEventPost.call_count, 2)
        self.assertFalse(pointer._pressed)


class PreviewWindowTests(unittest.TestCase):
    def test_close_processes_native_window_events(self):
        view = Preview.__new__(Preview)
        view.cv = Mock()
        view.close()
        self.assertEqual([call[0] for call in view.cv.method_calls], ['destroyWindow', 'waitKey'])
        view.cv.destroyWindow.assert_called_once_with(Preview.TITLE)
        view.cv.waitKey.assert_called_once_with(1)


    def test_preview_opens_small_and_resizable(self):
        cv = Mock()
        with patch.dict('sys.modules', cv2=cv, Quartz=Mock()):
            view = Preview(lambda text: text)
        view._escape_pressed = lambda: False
        cv.waitKey.return_value = -1
        cv.getWindowProperty.return_value = 1
        cv.resizeWindow.assert_not_called()
        view.update(np.zeros((480, 640, 3)), [], GestureState())
        view.update(np.zeros((480, 640, 3)), [], GestureState())
        cv.namedWindow.assert_called_once_with(Preview.TITLE, cv.WINDOW_NORMAL)
        cv.resizeWindow.assert_called_once_with(Preview.TITLE, 80, 60)
