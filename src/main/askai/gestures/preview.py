"""OpenCV preview and native mouse adapter; frames stay in memory."""
class Pointer:
    def __init__(self):
        import ctypes
        import sys
        if sys.platform != 'darwin':
            raise RuntimeError('Gesture mouse control currently requires macOS')
        services = ctypes.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        services.AXIsProcessTrusted.restype = ctypes.c_bool
        if not services.AXIsProcessTrusted():
            raise RuntimeError('Enable Accessibility permission for your terminal in macOS System Settings, then retry /gestures')
        import pyautogui
        self._mouse = pyautogui
        self._size = pyautogui.size()
        self._pressed = False
        self._position = None

    def move(self, x, y):
        # Keep the OS fail-safe corners reachable with the physical mouse.
        width, height = self._size
        position = (1 + x * (width - 3), 1 + y * (height - 3))
        if position == self._position:
            return
        if self._pressed:
            import Quartz
            event = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged,
                                                  position, Quartz.kCGMouseButtonLeft)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        else:
            self._mouse.moveTo(*position, _pause=False)
        self._position = position

    def press(self):
        if not self._pressed:
            self._pressed = True
            self._mouse.mouseDown(_pause=False)

    def release(self):
        if self._pressed:
            # Cleanup must work even with the physical pointer at a fail-safe corner.
            import Quartz
            event = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp,
                                                  Quartz.CGEventGetLocation(Quartz.CGEventCreate(None)),
                                                  Quartz.kCGMouseButtonLeft)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
            self._pressed = False

    def scroll(self, steps):
        self._mouse.scroll(steps, _pause=False)

    def scroll_boundary(self, edge):
        import Quartz
        self._send_key(126 if edge == 'top' else 125, Quartz.kCGEventFlagMaskCommand)

    def escape(self):
        self._send_key(53, 0)

    def _send_key(self, key, flags):
        import AppKit
        import Quartz
        application = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
        if application is None:
            raise RuntimeError('No focused application to receive Escape')
        pid = application.processIdentifier()
        for pressed in (True, False):
            event = Quartz.CGEventCreateKeyboardEvent(None, key, pressed)
            Quartz.CGEventSetFlags(event, flags)
            Quartz.CGEventPostToPid(pid, event)


class Preview:
    TITLE = 'AskAI Gestures'
    INITIAL_SIZE = (80, 60)
    LABELS = ('Scroll', 'No hand', 'Drag', 'Pinch', 'Move', 'Esc: stop', 'Hold thumbs up to stop', 'Hold open palm to send Esc', 'Hold phone gesture for voice')

    def __init__(self, translate):
        import cv2
        import Quartz
        self.cv = cv2
        self._escape_pressed = lambda: Quartz.CGEventSourceKeyState(Quartz.kCGEventSourceStateCombinedSessionState, 53)
        self._labels = {key: translate(key) for key in self.LABELS}
        cv2.namedWindow(self.TITLE, cv2.WINDOW_NORMAL)
        self._initial_resize_pending = True

    def prepare(self, frame):
        return self.cv.flip(frame, 1)

    def update(self, frame, points, state):
        height, width = frame.shape[:2]
        for x, y in points:
            self.cv.circle(frame, (int(x * width), int(y * height)), 4, (0, 255, 0), -1)
        label = 'Scroll' if state.scrolling else 'No hand' if state.pointer is None else 'Drag' if state.dragging else 'Pinch' if state.pinched else 'Move'
        self.cv.putText(frame, self._labels[label] + ' | ' + self._labels['Esc: stop'], (12, 28),
                       self.cv.FONT_HERSHEY_SIMPLEX, .7, (0, 255, 0), 2)
        progress = state.exit_progress if state.exit_progress is not None else state.escape_progress
        progress_label = 'Hold thumbs up to stop' if state.exit_progress is not None else 'Hold open palm to send Esc'
        if state.voice_progress is not None:
            progress = state.voice_progress
            progress_label = 'Hold phone gesture for voice'
        if progress is not None:
            bar_width = max(1, width - 24)
            self.cv.rectangle(frame, (12, 42), (12 + bar_width, 56), (80, 80, 80), -1)
            self.cv.rectangle(frame, (12, 42), (12 + int(bar_width * progress), 56),
                              (0, 200, 255), -1)
            self.cv.putText(frame, self._labels[progress_label] + f' {progress:.0%}',
                            (12, 82), self.cv.FONT_HERSHEY_SIMPLEX, .6, (0, 200, 255), 2)
        self.cv.imshow(self.TITLE, frame)
        if self._initial_resize_pending:
            self.cv.resizeWindow(self.TITLE, *self.INITIAL_SIZE)
            self._initial_resize_pending = False
        return (self.cv.waitKey(1) & 0xff != 27 and not self._escape_pressed()
                and self.cv.getWindowProperty(self.TITLE, self.cv.WND_PROP_VISIBLE) >= 1)

    def close(self):
        self.cv.destroyWindow(self.TITLE)
        # HighGUI needs an event cycle to finish closing the native macOS window.
        self.cv.waitKey(1)

