"""Phrase endpoint policy, independent of transcription providers and UI."""


def capture_phrase(recognizer, source, *, timeout, end_silence, phrase_limit=0, tail_margin=0):
    if end_silence <= 0 or phrase_limit < 0 or tail_margin < 0:
        raise ValueError('End silence must be positive; phrase limit and tail margin must be non-negative')
    recognizer.pause_threshold = end_silence
    recognizer.non_speaking_duration = min(recognizer.non_speaking_duration, end_silence)
    limit = phrase_limit + tail_margin if phrase_limit else None
    return recognizer.listen(source, timeout=timeout, phrase_time_limit=limit)
