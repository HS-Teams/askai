"""Frame public reasoning-summary deltas into readable debug messages."""
import re


class ReasoningSummaries:
    def __init__(self):
        self._text = {}
        self._shown = {}

    def append(self, item, index, delta):
        key = (item, index)
        self._text[key] = self._text.get(key, '') + delta
        offset = self._shown.get(key, 0)
        pending = self._text[key][offset:]
        boundaries = list(re.finditer(r'\n|[.!?](?=\s)', pending))
        if not boundaries:
            return []
        end = boundaries[-1].end()
        self._shown[key] = offset + end
        text = pending[:end].strip()
        return [text] if text else []

    def complete(self, item, summaries):
        result = []
        for index, text in enumerate(summaries):
            if not isinstance(text, str):
                continue
            key = (item, index)
            shown = self._shown.get(key, 0)
            received = self._text.get(key, '')
            # The completed item is authoritative; do not repeat an already shown section.
            tail = text[shown:] if text.startswith(received[:shown]) else ''
            if tail.strip():
                result.append(tail.strip())
            self._shown[key] = len(text)
            self._text[key] = text
        return result
