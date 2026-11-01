"""Phrase endpoint policy, independent of transcription providers and UI."""


class _FinishableStream:
    def __init__(self, stream, finish_requested):
        self._stream = stream
        self._finish_requested = finish_requested
        self._finished = False

    def read(self, size):
        self._finished = self._finished or self._finish_requested()
        return b'' if self._finished else self._stream.read(size)


def capture_phrase(recognizer, source, *, timeout, end_silence, phrase_limit=0, tail_margin=0,
                   finish_requested=None):
    if end_silence <= 0 or phrase_limit < 0 or tail_margin < 0:
        raise ValueError('End silence must be positive; phrase limit and tail margin must be non-negative')
    recognizer.pause_threshold = end_silence
    recognizer.non_speaking_duration = min(recognizer.non_speaking_duration, end_silence)
    limit = phrase_limit + tail_margin if phrase_limit else None
    if finish_requested is None:
        return recognizer.listen(source, timeout=timeout, phrase_time_limit=limit)
    stream = source.stream
    source.stream = _FinishableStream(stream, finish_requested)
    try:
        return recognizer.listen(source, timeout=timeout, phrase_time_limit=limit)
    finally:
        source.stream = stream
