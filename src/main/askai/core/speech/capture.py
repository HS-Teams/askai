"""Phrase endpoint policy, independent of transcription providers and UI."""
from collections import deque
import math

from speech_recognition import AudioData, WaitTimeoutError, audioop


MIN_SPEECH_WAIT_SECONDS = 3.0
END_SILENCE_SECONDS = 2.5
_FRAME_SECONDS = 0.02


class CaptureCancelled(Exception):
    """The user discarded the current recording."""


class _Phrase:
    def __init__(self, leading, minimum_speech):
        self.frames = list(leading)
        self.minimum_speech = minimum_speech
        self.duration = 0.0
        self.speech_duration = 0.0
        self.quiet_duration = 0.0
        self.last_speech = 0.0
        self.last_activity = 0.0
        self.confirmed = False

    def append(self, frame, duration, speaking):
        self.frames.append(frame)
        self.duration += duration
        if speaking:
            self.quiet_duration = 0.0
            self.last_activity = self.duration
            self.speech_duration += duration
            if self.speech_duration >= self.minimum_speech:
                self.confirmed = True
                self.last_speech = self.duration
        else:
            self.quiet_duration += duration
            if self.quiet_duration >= self.minimum_speech:
                self.speech_duration = 0.0

    def ended(self, end_silence):
        # Let a new word finish being classified before deciding to stop.
        return (self.speech_duration == 0 and
                self.duration - self.last_speech >= end_silence)

    def audio(self, source, trailing=None):
        data = b''.join(self.frames)
        if trailing is not None:
            # Keep short final words even when they do not reset the pause timer.
            trim_seconds = max(0.0, self.duration - self.last_activity - trailing)
            trim_bytes = int(trim_seconds * source.SAMPLE_RATE) * source.SAMPLE_WIDTH
            if trim_bytes:
                data = data[:-trim_bytes]
        return AudioData(data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)


def _adjust_waiting_threshold(recognizer, energy, duration):
    if recognizer.dynamic_energy_threshold:
        damping = recognizer.dynamic_energy_adjustment_damping ** duration
        target = energy * recognizer.dynamic_energy_ratio
        recognizer.energy_threshold = recognizer.energy_threshold * damping + target * (1 - damping)


def capture_phrase(recognizer, source, *, timeout, end_silence, phrase_limit=0, tail_margin=0,
                   cancel_requested=None):
    if end_silence <= 0 or phrase_limit < 0 or tail_margin < 0:
        raise ValueError('End silence must be positive; phrase limit and tail margin must be non-negative')
    frame_size = min(source.CHUNK, max(1, int(source.SAMPLE_RATE * _FRAME_SECONDS)))
    frame_seconds = frame_size / source.SAMPLE_RATE
    trailing = min(recognizer.non_speaking_duration, end_silence)
    leading = deque(maxlen=math.ceil(trailing / frame_seconds))
    limit = phrase_limit + tail_margin if phrase_limit else None
    elapsed = 0.0
    phrase = None
    while True:
        if cancel_requested is not None and cancel_requested():
            raise CaptureCancelled()
        if phrase is None and timeout is not None and elapsed >= timeout:
            raise WaitTimeoutError('listening timed out while waiting for phrase to start')
        frame = source.stream.read(frame_size)
        if not frame:
            break
        duration = len(frame) / (source.SAMPLE_RATE * source.SAMPLE_WIDTH)
        elapsed += duration
        energy = audioop.rms(frame, source.SAMPLE_WIDTH)
        speaking = energy > recognizer.energy_threshold
        if phrase is None:
            if not speaking:
                leading.append(frame)
                _adjust_waiting_threshold(recognizer, energy, duration)
                continue
            phrase = _Phrase(leading, recognizer.phrase_threshold)
            leading.clear()
        # The calibrated threshold stays fixed during a phrase: speech must not
        # raise it, and quiet pauses must not lower it until noise counts as speech.
        phrase.append(frame, duration, speaking)
        if limit is not None and phrase.duration >= limit:
            return phrase.audio(source)
        if phrase.ended(end_silence):
            if phrase.confirmed:
                return phrase.audio(source, trailing)
            phrase = None
    return phrase.audio(source) if phrase else AudioData(b'', source.SAMPLE_RATE, source.SAMPLE_WIDTH)
