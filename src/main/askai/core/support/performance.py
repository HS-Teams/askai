"""Measure local stages without logging prompts, answers or credentials."""
from contextlib import contextmanager
import logging
from time import perf_counter


@contextmanager
def timed(stage):
    started = perf_counter()
    try:
        yield
    finally:
        logging.debug('AskAI timing %s: %.3fs', stage, perf_counter() - started)
