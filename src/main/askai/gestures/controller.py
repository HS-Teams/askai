"""Pure gesture state and normalized pointer coordinates; no camera or UI."""
from dataclasses import dataclass
from math import dist, hypot, isfinite
from time import monotonic
from askai.gestures.pointer_response import PointerResponse
from askai.gestures.scroll import ScrollMotion, is_scroll_hand
from askai.gestures.phone import is_phone_hand
from askai.gestures.palm import is_open_palm
from askai.gestures.rock import is_rock_hand
from askai.gestures.thumbs_up import is_thumbs_up


@dataclass(frozen=True)
class GestureState:
    pointer: tuple[float, float] | None = None
    dragging: bool = False
    pinched: bool = False
    exit_progress: float | None = None
    exit_requested: bool = False
    abort_progress: float | None = None
    abort_requested: bool = False
    voice_progress: float | None = None
    voice_requested: bool = False
    double_click_progress: float | None = None
    double_click_requested: bool = False
    scrolling: bool = False
    scroll_steps: int = 0
    scroll_boundary: str | None = None


class GestureController:
    SCROLL_COOLDOWN_SECONDS = .5
    EXIT_HOLD_SECONDS = .5
    ABORT_HOLD_SECONDS = .5
    DOUBLE_CLICK_HOLD_SECONDS = .5
    DRAG_HOLD_SECONDS = .5
    PINCH_COOLDOWN_SECONDS = 1.0
    ABORT_COOLDOWN_SECONDS = 1.0
    DOUBLE_CLICK_COOLDOWN_SECONDS = 1.0
    CLOSE_RATIO = .35
    OPEN_RATIO = .50
    SMOOTHING = .18 * 1.10
    FINE_POINTER_DISTANCE = .05
    FINE_POINTER_MIN_FACTOR = .01
    DEAD_ZONE = .008
    CAMERA_MARGIN = .25

    def __init__(self, clock=monotonic, motion_clock=monotonic):
        self._clock = clock
        self._motion_clock = motion_clock
        self._dragging = False
        self._pinch_ready_at = float('-inf')
        self._abort_ready_at = float('-inf')
        self._double_ready_at = float('-inf')
        self.reset()

    def reset(self):
        self._end_pinch()
        self._response = PointerResponse(self.SMOOTHING, self.DEAD_ZONE, self._motion_clock)
        self._voice_started = None
        self._voice_sent = False
        self._scroll = ScrollMotion(self._clock)
        self._scroll_mode = False
        self._scroll_missing_since = None
        self._exit_started = None
        self._abort_started = None
        self._abort_sent = False
        self._double_started = None
        self._double_sent = False
        self._pointer = None
        self._armed = False
        self._dragging = False
        self._drag_anchor = None
        self._drag_origin = None
        self._drag_waist = None
        self._pinch_started = None

    def suspend(self):
        """Cancel gestures outside the control area while retaining the cursor target."""
        pointer = self._pointer
        state = self._tracking_lost()
        self._pointer = pointer
        return state

    def update(self, points, aspect=1.0, *, world_points, waist):
        if (len(points) != 21 or not all(len(point) == 2 and all(isfinite(v) for v in point) for point in points)
                or len(world_points) != 21
                or not all(len(point) == 3 and all(isfinite(v) for v in point) for point in world_points)
                or not isfinite(aspect) or aspect <= 0):
            return self._tracking_lost()
        world_scale = dist(world_points[5], world_points[17])
        if not isfinite(world_scale) or world_scale <= 0:
            return self._tracking_lost()
        # Rotation can overlap separated fingertips in the image. Measure contact in 3D.
        ratio = dist(world_points[4], world_points[8]) / world_scale
        if not isfinite(ratio):
            return self._tracking_lost()
        commands_allowed = ratio >= self.OPEN_RATIO
        scroll_gesture = commands_allowed and is_scroll_hand(world_points)
        if scroll_gesture:
            if not self._scroll_mode:
                self._scroll.reset()
            self._scroll_mode = True
            self._scroll_missing_since = None
            self._exit_started = self._abort_started = self._double_started = self._voice_started = None
            self._abort_sent = self._double_sent = self._voice_sent = False
            self._armed = False
            self._end_pinch()
            steps = self._scroll.update(points[0][1])
            return GestureState(scrolling=True, scroll_steps=steps, scroll_boundary=self._scroll.boundary)
        self._stop_scroll()
        if self._scroll_mode:
            return GestureState(scrolling=True)
        scale = hypot((points[5][0] - points[17][0]) * aspect, points[5][1] - points[17][1])
        if scale < .01:
            return self._tracking_lost()
        palm_gesture = commands_allowed and is_open_palm(points, aspect)
        rock_gesture = commands_allowed and is_rock_hand(world_points)
        if not palm_gesture:
            self._double_started = None
            self._double_sent = False
        if not rock_gesture:
            self._abort_started = None
            self._abort_sent = False
        if not is_phone_hand(points, aspect):
            self._voice_started = None
            self._voice_sent = False
        if commands_allowed and is_thumbs_up(points, aspect):
            self._abort_started = None
            self._abort_sent = False
            now = self._clock()
            if self._exit_started is None:
                self._exit_started = now
            progress = min(1., max(0., (now - self._exit_started) / self.EXIT_HOLD_SECONDS))
            self._armed = False
            self._end_pinch()
            self._drag_anchor = self._drag_origin = None
            self._scroll.reset()
            return GestureState(exit_progress=progress, exit_requested=progress >= 1., scrolling=self._scroll_mode)
        self._exit_started = None
        if commands_allowed and is_phone_hand(points, aspect):
            now = self._clock()
            if self._voice_started is None:
                self._voice_started = now
            progress = min(1., max(0., (now - self._voice_started) / self.EXIT_HOLD_SECONDS))
            send = progress >= 1. and not self._voice_sent
            self._voice_sent = self._voice_sent or send
            self._abort_started = None
            self._abort_sent = False
            self._armed = False
            self._end_pinch()
            return GestureState(voice_progress=progress, voice_requested=send)
        self._voice_started = None
        self._voice_sent = False
        if palm_gesture:
            now = self._clock()
            if self._double_started is None:
                self._double_started = now
            progress = min(1., max(0., (now - self._double_started) / self.DOUBLE_CLICK_HOLD_SECONDS))
            send = progress >= 1. and not self._double_sent and now >= self._double_ready_at
            self._double_sent = self._double_sent or send
            if send:
                self._double_ready_at = now + self.DOUBLE_CLICK_COOLDOWN_SECONDS
            self._armed = False
            self._end_pinch()
            return GestureState(double_click_progress=progress, double_click_requested=send)
        if rock_gesture:
            now = self._clock()
            if self._abort_started is None:
                self._abort_started = now
            progress = min(1., max(0., (now - self._abort_started) / self.ABORT_HOLD_SECONDS))
            send = progress >= 1. and not self._abort_sent and now >= self._abort_ready_at
            self._abort_sent = self._abort_sent or send
            if send:
                self._abort_ready_at = now + self.ABORT_COOLDOWN_SECONDS
            self._armed = False
            self._end_pinch()
            return GestureState(abort_progress=progress, abort_requested=send)
        self._abort_started = None
        self._abort_sent = False
        x, y = points[8]
        active_span = 1. - 2. * self.CAMERA_MARGIN
        # Keep space below the screen's bottom target for closing the pinch above the hips.
        mapping_waist = self._drag_waist if self._dragging else waist
        waist_height = mapping_waist.height_at(x)
        if not isfinite(waist_height) or waist_height <= 0:
            return self._tracking_lost()
        top = self.CAMERA_MARGIN * waist_height
        bottom = (1. - self.CAMERA_MARGIN) * waist_height
        hand_position = ((x - self.CAMERA_MARGIN) / active_span,
                         (y - top) / (bottom - top))
        was_dragging = self._dragging
        if ratio >= self.OPEN_RATIO:
            self._end_pinch()
            self._armed = True
        elif ratio <= self.CLOSE_RATIO and self._armed:
            self._armed = False
            self._dragging = self._clock() >= self._pinch_ready_at
        starting = self._dragging and not was_dragging
        releasing = was_dragging and not self._dragging
        if self._pointer is None:
            self._pointer = tuple(max(0., min(1., v)) for v in hand_position)
        if starting:
            self._drag_waist = waist
            self._pinch_started = self._clock()
            self._drag_origin = self._pointer
            self._drag_anchor = hand_position
        waiting_for_drag = self._dragging and self._clock() - self._pinch_started < self.DRAG_HOLD_SECONDS
        if waiting_for_drag:
            # Ignore finger movement during click confirmation.
            self._drag_anchor = hand_position
        target = hand_position
        if self._dragging:
            target = tuple(origin + current - anchor for origin, current, anchor
                           in zip(self._drag_origin, hand_position, self._drag_anchor))
        target = tuple(max(0., min(1., value)) for value in target)
        response = self._response.sample(hand_position, frozen=starting or releasing or waiting_for_drag)
        distance = hypot(target[0] - self._pointer[0], target[1] - self._pointer[1])
        if not self._dragging and distance < self.FINE_POINTER_DISTANCE:
            fraction = distance / self.FINE_POINTER_DISTANCE
            response *= self.FINE_POINTER_MIN_FACTOR + (1. - self.FINE_POINTER_MIN_FACTOR) * fraction ** 2
        if (not starting and not releasing and not waiting_for_drag
                and distance > self.DEAD_ZONE):
            self._pointer = tuple(a + response * (b - a) for a, b in zip(self._pointer, target))
        if not starting and not releasing and not waiting_for_drag:
            # Reach screen edges exactly rather than stopping inside the dead zone.
            self._pointer = tuple(b if b in (0., 1.) and abs(b - a) <= self.DEAD_ZONE else a
                                  for a, b in zip(self._pointer, target))
        return GestureState(self._pointer, self._dragging, self._dragging)

    def _stop_scroll(self):
        if not self._scroll_mode:
            return
        now = self._clock()
        if self._scroll_missing_since is None:
            self._scroll_missing_since = now
        if now - self._scroll_missing_since >= self.SCROLL_COOLDOWN_SECONDS:
            self._scroll_mode = False
            self._scroll_missing_since = None
            self._scroll.reset()

    def _tracking_lost(self):
        self._stop_scroll()
        mode, missing_since, scroll = self._scroll_mode, self._scroll_missing_since, self._scroll
        pointer = self._pointer
        self.reset()
        self._scroll_mode, self._scroll_missing_since, self._scroll = mode, missing_since, scroll
        if mode:
            self._pointer = pointer
        return GestureState(scrolling=mode)

    def _end_pinch(self):
        if self._dragging:
            self._pinch_ready_at = self._clock() + self.PINCH_COOLDOWN_SECONDS
            self._dragging = False
