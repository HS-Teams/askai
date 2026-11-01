"""Normalize provider quotas without generating text, speech or session turns."""
from dataclasses import dataclass
from datetime import datetime
import math


@dataclass(frozen=True)
class Usage:
    provider: str
    remaining: str
    window: str = '-'
    resets_at: int | None = None
    error: str | None = None


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Provider did not return valid usage limits')
    return value


def codex_usage(payload):
    buckets = payload.get('rateLimitsByLimitId') or {'codex': payload.get('rateLimits')}
    rows = []
    for key, bucket in buckets.items():
        if not isinstance(bucket, dict):
            continue
        provider = 'Codex / ' + (bucket.get('limitName') or key)
        for name in ('primary', 'secondary'):
            window = bucket.get(name)
            if not window:
                continue
            used = _number(window.get('usedPercent'))
            minutes = window.get('windowDurationMins')
            duration = f'{_number(minutes):g} min' if minutes is not None else name
            rows.append(Usage(provider, f'{max(0, min(100, 100-used)):g}%', duration, window.get('resetsAt')))
    if not rows:
        raise ValueError('Codex did not return quota windows')
    return rows


def elevenlabs_usage(payload):
    used, limit = _number(payload.get('character_count')), _number(payload.get('character_limit'))
    return [Usage('ElevenLabs', _remaining_percent(used, limit),
                  'characters', payload.get('next_character_count_reset_unix'))]


def deepl_usage(quota):
    if not quota.valid:
        raise ValueError('DeepL did not return character usage limits')
    used, limit = _number(quota.count), _number(quota.limit)
    return [Usage('DeepL', _remaining_percent(used, limit), 'characters')]


def _remaining_percent(used, limit):
    if limit <= 0:
        raise ValueError('Provider did not return a positive usage limit')
    return f'{max(0, min(100, (limit-used) / limit * 100)):.2f}%'


def read_usage(provider, read):
    """A failed provider must not hide the other provider's balance."""
    try:
        return read()
    except (RuntimeError, OSError, ValueError, KeyError, TypeError) as error:
        return [Usage(provider, '', error=str(error))]


def engine_usage(provider, engine):
    backend = getattr(engine, 'backend', engine)
    reader = getattr(backend, 'usage', None)
    if reader is None:
        return [Usage(provider, '', error='Usage reporting is not supported by this engine')]
    return read_usage(provider, reader)


def reset_time(timestamp):
    if timestamp is None:
        return '-'
    return datetime.fromtimestamp(_number(timestamp)).astimezone().strftime('%d/%m/%Y %H:%M %Z')
