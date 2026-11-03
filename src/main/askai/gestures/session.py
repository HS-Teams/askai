"""Coordinate injected capture, detector, pointer and view without owning UI."""
from time import monotonic
from math import dist, isfinite, hypot
from askai.gestures.controller import GestureController, GestureState
from askai.gestures.scroll import is_scroll_hand

INACTIVITY_SECONDS = 2.5
RESUME_HOLD_SECONDS = 2.5
PAUSE_WARNING_SECONDS = 45.0
PAUSE_STOP_SECONDS = 60.0

GRANTS = ('camera.preview.local', 'desktop.pointer.move', 'desktop.pointer.click', 'desktop.pointer.scroll', 'microphone.listen.local')


def authorize(policy, interact):
    return policy.authorize(GRANTS,
        'Allow local camera preview and mouse movement/clicks, scrolling, voice input and aborting the current AskAI operation by hand gestures until Esc? No video is recorded or shared.',
        interact)


def run_session(camera, tracker, pointer, view, policy, notify=lambda kind: None, should_stop=lambda: False,
                clock=monotonic, should_pause=lambda: False):
    controller = GestureController(clock)
    last_recognized = clock()
    waiting = False
    paused_since = None
    pause_warned = False
    resume_since = None
    waist_warned = False
    waist_recovered_since = None
    pressed = False
    scrolling = False
    scroll_direction = 0
    ptt_paused = False
    try:
        while not should_stop():
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError('Cannot read the gesture camera')
            image_points, world_points, waist = tracker.detect(frame)
            points = [(1 - x, y) for x, y in image_points]
            waist = waist.mirrored() if waist is not None else None
            frame = view.prepare(frame)
            now = clock()
            if should_pause():
                if not ptt_paused:
                    pointer.release()
                    controller.reset()
                    pressed = scrolling = False
                    scroll_direction = 0
                    notify('ptt_paused')
                ptt_paused = waiting = True
                paused_since = last_recognized = now
                pause_warned = False
                resume_since = waist_recovered_since = None
                if not view.update(frame, points, GestureState(), waist):
                    return
                continue
            if ptt_paused:
                ptt_paused = False
                paused_since = now
            if waist is None and not waist_warned:
                notify('waist_missing')
                waist_warned = True
            if waiting and now - paused_since >= PAUSE_STOP_SECONDS:
                return
            aspect = frame.shape[1] / frame.shape[0]
            inside = waist is not None and waist.allows(points)
            recognized = (inside and all(isfinite(v) for point in points for v in point)
                          and len(world_points) == 21
                          and all(len(point) == 3 and all(isfinite(v) for v in point) for point in world_points)
                          and 0 < dist(world_points[5], world_points[17]) < float('inf')
                          and (hypot((points[5][0] - points[17][0]) * aspect,
                                     points[5][1] - points[17][1]) >= .01
                               or is_scroll_hand(world_points)))
            if recognized:
                last_recognized = now
                if waist_warned:
                    if waist_recovered_since is None:
                        waist_recovered_since = now
                    if now - waist_recovered_since >= RESUME_HOLD_SECONDS:
                        waist_warned = False
                        waist_recovered_since = None
                if waiting:
                    if resume_since is None:
                        resume_since = now
                    if now - resume_since >= RESUME_HOLD_SECONDS:
                        waiting = False
                        paused_since = None
                        pause_warned = False
                        resume_since = None
                        notify('resumed')
            else:
                waist_recovered_since = None
                resume_since = None
                if not waiting and now - last_recognized >= INACTIVITY_SECONDS:
                    waiting = True
                    paused_since = now
                    pointer.release()
                    controller.reset()
                    pressed = scrolling = False
                    scroll_direction = 0
                    notify('inactive')
            if waiting:
                paused_for = now - paused_since
                if paused_for >= PAUSE_WARNING_SECONDS and not pause_warned:
                    pause_warned = True
                    notify('inactivity_warning')
            if not inside:
                state = controller.suspend()
            elif waiting:
                state = GestureState()
            else:
                state = controller.update(points, aspect, world_points=world_points, waist=waist)
            if not view.update(frame, points, state, waist):
                return
            if waiting:
                continue
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
            if state.abort_requested:
                notify('abort')
            if state.scrolling != scrolling:
                notify('scroll_start' if state.scrolling else 'scroll_stop')
                scrolling = state.scrolling
                scroll_direction = 0
            if state.scroll_boundary:
                pointer.scroll_boundary(state.scroll_boundary)
            if state.scroll_steps:
                pointer.scroll(state.scroll_steps)
                direction = 1 if state.scroll_steps > 0 else -1
                if direction != scroll_direction:
                    notify('scroll_up' if direction > 0 else 'scroll_down')
                    scroll_direction = direction
            if state.pointer and not state.scrolling:
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
