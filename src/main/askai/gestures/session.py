"""Coordinate injected capture, detector, pointer and view without owning UI."""
from time import monotonic
from math import isfinite, hypot
from askai.gestures.controller import GestureController

INACTIVITY_SECONDS = 5.0

GRANTS = ('camera.preview.local', 'desktop.pointer.move', 'desktop.pointer.click', 'desktop.keyboard.escape', 'desktop.pointer.scroll', 'microphone.listen.local')


def authorize(policy, interact):
    return policy.authorize(GRANTS,
        'Allow local camera preview and mouse movement/clicks, scrolling, voice input and sending Escape by hand gestures until Esc? No video is recorded or shared.',
        interact)


def run_session(camera, tracker, pointer, view, policy, notify=lambda kind: None, should_stop=lambda: False, clock=monotonic):
    controller = GestureController(clock)
    last_recognized = clock()
    pressed = False
    scrolling = False
    scroll_direction = 0
    try:
        while not should_stop():
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError('Cannot read the gesture camera')
            points = [(1 - x, y) for x, y in tracker.detect(frame)]
            frame = view.prepare(frame)
            state = controller.update(points, frame.shape[1] / frame.shape[0])
            if not view.update(frame, points, state):
                return
            now = clock()
            aspect = frame.shape[1] / frame.shape[0]
            recognized = (len(points) == 21 and all(isfinite(v) for point in points for v in point)
                          and hypot((points[5][0] - points[17][0]) * aspect,
                                    points[5][1] - points[17][1]) >= .01)
            if recognized:
                last_recognized = now
            elif now - last_recognized > INACTIVITY_SECONDS:
                notify('inactive')
                return
            if state.exit_requested:
                notify('exit')
                return
            policy.pending(GRANTS)  # Recheck denials; 'ask' was authorized for this session.
            if not state.dragging:
                pointer.release()
            if state.double_click_requested:
                pointer.double_click()
                notify('double_click')
            if state.voice_requested:
                notify('voice')
            if state.escape_requested:
                pointer.escape()
                notify('escape')
            if state.scrolling != scrolling:
                notify('scroll_start' if state.scrolling else 'scroll_stop')
                scrolling = state.scrolling
                scroll_direction = 0
            if state.scroll_boundary:
                pointer.scroll_boundary(state.scroll_boundary)
                notify('scroll_' + state.scroll_boundary)
            if state.scroll_steps:
                pointer.scroll(state.scroll_steps)
                direction = 1 if state.scroll_steps > 0 else -1
                if direction != scroll_direction:
                    notify('scroll_up' if direction > 0 else 'scroll_down')
                    scroll_direction = direction
            if state.pointer:
                pointer.move(*state.pointer)
            if state.dragging:
                pointer.press()
            if state.dragging != pressed:
                notify('pinch' if state.dragging else 'release')
                pressed = state.dragging
    finally:
        try:
            try:
                pointer.release()
            finally:
                camera.release()
        finally:
            try:
                tracker.close()
            finally:
                view.close()
