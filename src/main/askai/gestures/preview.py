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
        import Quartz
        error, displays, _ = Quartz.CGGetActiveDisplayList(32, None, None)
        if error or not displays:
            raise RuntimeError("Cannot determine active display bounds")
        self._screens = [Quartz.CGDisplayBounds(display) for display in displays]
        self._pressed = False
        self._position = None

    def move(self, x, y):
        # Keep the OS fail-safe corners reachable with the physical mouse.
        left = min(r.origin.x for r in self._screens)
        top = min(r.origin.y for r in self._screens)
        right = max(r.origin.x + r.size.width for r in self._screens)
        bottom = max(r.origin.y + r.size.height for r in self._screens)
        target = (left + x * (right - left - 1), top + y * (bottom - top - 1))
        # Project gaps between differently sized displays onto the nearest screen.
        candidates = [(max(r.origin.x + 1, min(target[0], r.origin.x + r.size.width - 2)),
                       max(r.origin.y + 1, min(target[1], r.origin.y + r.size.height - 2)))
                      for r in self._screens]
        position = min(candidates, key=lambda p: (p[0]-target[0])**2 + (p[1]-target[1])**2)
        if position == self._position:
            return
        if self._pressed:
            from math import hypot
            if not self._sound_dragged and (self._sound_origin is None or
                    hypot(position[0] - self._sound_origin[0], position[1] - self._sound_origin[1]) > 4.):
                from askai.gestures.sfx import play_drag
                self._sound_dragged = True
                play_drag()
            import Quartz
            event = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged,
                                                  position, Quartz.kCGMouseButtonLeft)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        else:
            import Quartz
            event = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved,
                                                  position, Quartz.kCGMouseButtonLeft)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        self._position = position

    def press(self):
        if not self._pressed:
            self._pressed = True
            self._sound_origin = self._position
            self._sound_dragged = False
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
            if not self._sound_dragged:
                from askai.gestures.sfx import play_click
                play_click()

    def double_click(self):
        import Quartz
        from askai.gestures.sfx import play_click
        self.release()
        location = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
        for count in (1, 2):
            for kind in (Quartz.kCGEventLeftMouseDown, Quartz.kCGEventLeftMouseUp):
                event = Quartz.CGEventCreateMouseEvent(None, kind, location, Quartz.kCGMouseButtonLeft)
                Quartz.CGEventSetIntegerValueField(event, Quartz.kCGMouseEventClickState, count)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
            play_click()

    def scroll(self, steps):
        self._mouse.scroll(steps, _pause=False)

    def scroll_boundary(self, edge):
        import Quartz
        self._send_key(126 if edge == 'top' else 125, Quartz.kCGEventFlagMaskCommand)

    def escape(self):
        self._send_key(53, 0)
        from askai.gestures.sfx import play_escape
        play_escape()

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
    LABELS = ('Scroll', 'No hand', 'Drag', 'Pinch', 'Move', 'Esc: stop', 'Hold thumbs up to stop',
              'Hold heavy metal for 1s to send Esc', 'Hold open palm for 1s to double-click', 'Hold phone gesture for voice',
              'Waist not visible')

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

    def update(self, frame, points, state, waist=None):
        height, width = frame.shape[:2]
        if waist is not None:
            self.cv.line(frame, (0, int(height * waist.height_at(0))),
                         (width - 1, int(height * waist.height_at(1))), (0, 200, 255), 2)
        for x, y in points:
            self.cv.circle(frame, (int(x * width), int(y * height)), 4, (0, 255, 0), -1)
        label = 'Scroll' if state.scrolling else 'No hand' if state.pointer is None else 'Drag' if state.dragging else 'Pinch' if state.pinched else 'Move'
        if waist is None:
            label = 'Waist not visible'
        self.cv.putText(frame, self._labels[label] + ' | ' + self._labels['Esc: stop'], (12, 28),
                       self.cv.FONT_HERSHEY_SIMPLEX, .7, (0, 255, 0), 2)
        progress = state.exit_progress if state.exit_progress is not None else state.escape_progress
        progress_label = 'Hold thumbs up to stop' if state.exit_progress is not None else 'Hold heavy metal for 1s to send Esc'
        if state.double_click_progress is not None:
            progress = state.double_click_progress
            progress_label = 'Hold open palm for 1s to double-click'
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
        key = self.cv.waitKey(1) & 0xff
        return (key != 27 and not self._escape_pressed()
                and self.cv.getWindowProperty(self.TITLE, self.cv.WND_PROP_VISIBLE) >= 1)

    def close(self):
        self.cv.destroyWindow(self.TITLE)
        # HighGUI needs an event cycle to finish closing the native macOS window.
        self.cv.waitKey(1)

