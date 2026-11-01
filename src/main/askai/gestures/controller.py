"""Pure gesture state and normalized pointer coordinates; no camera or UI."""
from dataclasses import dataclass
from math import hypot, isfinite
from time import monotonic
from askai.gestures.scroll import ScrollMotion, is_scroll_hand
from askai.gestures.phone import is_phone_hand
from askai.gestures.palm import is_open_palm
from askai.gestures.thumbs_up import is_thumbs_up


@dataclass(frozen=True)
class GestureState:
    pointer: tuple[float, float] | None = None
    dragging: bool = False
    pinched: bool = False
    exit_progress: float | None = None
    exit_requested: bool = False
    escape_progress: float | None = None
    escape_requested: bool = False
    voice_progress: float | None = None
    voice_requested: bool = False
    scrolling: bool = False
    scroll_steps: int = 0
    scroll_boundary: str | None = None


class GestureController:
    SCROLL_COOLDOWN_SECONDS = .5
    SCROLL_IDLE_SECONDS = .5
    EXIT_HOLD_SECONDS = .5
    DRAG_HOLD_SECONDS = .5
    CLOSE_RATIO = .35
    OPEN_RATIO = .50
    SMOOTHING = .18
    DEAD_ZONE = .008
    CAMERA_MARGIN = .25

    def __init__(self, clock=monotonic):
        self._clock = clock
        self.reset()

    def reset(self):
        self._voice_started = None
        self._voice_sent = False
        self._scroll = ScrollMotion(self._clock)
        self._scroll_idle_since = None
        self._scroll_mode = False
        self._scroll_seen = False
        self._scroll_toggled_at = None
        self._exit_started = None
        self._escape_started = None
        self._escape_sent = False
        self._pointer = None
        self._armed = False
        self._dragging = False
        self._drag_anchor = None
        self._drag_origin = None
        self._pinch_started = None

    def update(self, points, aspect=1.0):
        if (len(points) != 21 or not all(isfinite(v) for point in points for v in point)
                or not isfinite(aspect) or aspect <= 0):
            return self._tracking_lost()
        def distance(a, b):
            return hypot((points[a][0] - points[b][0]) * aspect, points[a][1] - points[b][1])
        scale = distance(5, 17)
        if scale < .01:
            return self._tracking_lost()
        ratio = distance(4, 8) / scale
        commands_allowed = ratio >= self.OPEN_RATIO
        if not is_phone_hand(points, aspect):
            self._voice_started = None
            self._voice_sent = False
        scroll_gesture = commands_allowed and is_scroll_hand(points, aspect)
        now = self._clock() if scroll_gesture or self._scroll_mode or self._scroll_toggled_at is not None else None
        cooled_down = (self._scroll_toggled_at is None
                       or now - self._scroll_toggled_at >= self.SCROLL_COOLDOWN_SECONDS)
        if scroll_gesture and not self._scroll_seen and cooled_down:
            self._scroll_mode = not self._scroll_mode
            self._scroll_toggled_at = now
            self._scroll_idle_since = now
            self._scroll.reset()
            self._exit_started = self._escape_started = None
            self._escape_sent = False
            self._armed = self._dragging = False
        self._scroll_seen = scroll_gesture
        if commands_allowed and is_thumbs_up(points, aspect):
            self._escape_started = None
            self._escape_sent = False
            now = self._clock()
            if self._exit_started is None:
                self._exit_started = now
            progress = min(1., max(0., (now - self._exit_started) / self.EXIT_HOLD_SECONDS))
            self._armed = False
            self._dragging = False
            self._drag_anchor = self._drag_origin = None
            self._scroll.reset()
            return GestureState(exit_progress=progress, exit_requested=progress >= 1., scrolling=self._scroll_mode)
        self._exit_started = None
        if self._scroll_mode:
            steps = self._scroll.update(points[0][1])
            if steps or self._scroll.boundary:
                self._scroll_idle_since = now
            elif self._scroll_idle_since is not None and now - self._scroll_idle_since >= self.SCROLL_IDLE_SECONDS:
                self._scroll_mode = False
                self._scroll_toggled_at = now
                self._scroll.reset()
                return GestureState()
            return GestureState(scrolling=True, scroll_steps=steps, scroll_boundary=self._scroll.boundary)
        if self._scroll_toggled_at is not None and now - self._scroll_toggled_at < self.SCROLL_COOLDOWN_SECONDS:
            return GestureState()
        if commands_allowed and is_phone_hand(points, aspect):
            now = self._clock()
            if self._voice_started is None:
                self._voice_started = now
            progress = min(1., max(0., (now - self._voice_started) / self.EXIT_HOLD_SECONDS))
            send = progress >= 1. and not self._voice_sent
            self._voice_sent = self._voice_sent or send
            self._escape_started = None
            self._escape_sent = False
            self._armed = self._dragging = False
            return GestureState(voice_progress=progress, voice_requested=send)
        self._voice_started = None
        self._voice_sent = False
        if commands_allowed and is_open_palm(points, aspect):
            now = self._clock()
            if self._escape_started is None:
                self._escape_started = now
            progress = min(1., max(0., (now - self._escape_started) / self.EXIT_HOLD_SECONDS))
            send = progress >= 1. and not self._escape_sent
            self._escape_sent = self._escape_sent or send
            self._armed = self._dragging = False
            return GestureState(escape_progress=progress, escape_requested=send)
        self._escape_started = None
        self._escape_sent = False
        x, y = points[8]
        active_span = 1. - 2. * self.CAMERA_MARGIN
        hand_position = tuple((v - self.CAMERA_MARGIN) / active_span for v in (x, y))
        was_dragging = self._dragging
        if ratio >= self.OPEN_RATIO:
            self._dragging = False
            self._armed = True
        elif ratio <= self.CLOSE_RATIO and self._armed:
            self._dragging = True
            self._armed = False
        starting = self._dragging and not was_dragging
        releasing = was_dragging and not self._dragging
        if self._pointer is None:
            self._pointer = tuple(max(0., min(1., v)) for v in hand_position)
        if starting:
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
        if (not starting and not releasing and not waiting_for_drag
                and hypot(target[0] - self._pointer[0], target[1] - self._pointer[1]) > self.DEAD_ZONE):
            self._pointer = tuple(a + self.SMOOTHING * (b - a) for a, b in zip(self._pointer, target))
        if not starting and not releasing and not waiting_for_drag:
            # Reach screen edges exactly rather than stopping inside the dead zone.
            self._pointer = tuple(b if b in (0., 1.) and abs(b - a) <= self.DEAD_ZONE else a
                                  for a, b in zip(self._pointer, target))
        return GestureState(self._pointer, self._dragging, self._dragging)

    def _tracking_lost(self):
        idle_since = self._scroll_idle_since
        mode, seen, toggled_at = self._scroll_mode, self._scroll_seen, self._scroll_toggled_at
        self.reset()
        self._scroll_mode, self._scroll_seen, self._scroll_toggled_at = mode, seen, toggled_at
        self._scroll_idle_since = idle_since
        if mode and idle_since is not None and self._clock() - idle_since >= self.SCROLL_IDLE_SECONDS:
            self._scroll_mode = False
            self._scroll_toggled_at = self._clock()
        return GestureState(scrolling=self._scroll_mode)
