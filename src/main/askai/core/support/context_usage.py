"""Present the latest runtime context measurement without estimating model limits."""
from askai.core.support.number_format import compact_count


def context_label(engine, translate):
    backend = getattr(engine, 'backend', None)
    reader = getattr(backend, 'context_usage', None)
    usage = reader() if reader else None
    label = ''
    if usage is None:
        return label + translate('Awaiting data' if reader else 'Not reported')
    used, limit = usage['used'], usage['limit']
    return (label + f'{compact_count(used)} / {compact_count(limit)} · '
            + f'{used / limit * 100:.0f}% ' + translate('used') + ' · '
            + compact_count(max(0, limit - used)) + ' ' + translate('free'))
