"""Measure local stages without logging prompts, answers or credentials."""
from contextlib import contextmanager
from contextvars import ContextVar
import logging
from time import perf_counter
from uuid import uuid4


_request_id = ContextVar('askai_timing_request', default='-')


def record_timing(stage, elapsed, *, outcome='completed'):
    logging.info('AskAI timing %s: %.3fs request=%s outcome=%s',
                 stage, elapsed, _request_id.get(), outcome)


@contextmanager
def request_timing():
    token = _request_id.set(uuid4().hex[:12])
    try:
        with timed('request.total'):
            yield
    finally:
        _request_id.reset(token)


@contextmanager
def timed(stage):
    started = perf_counter()
    outcome = 'completed'
    try:
        yield
    except BaseException:
        outcome = 'failed'
        raise
    finally:
        record_timing(stage, perf_counter() - started, outcome=outcome)
