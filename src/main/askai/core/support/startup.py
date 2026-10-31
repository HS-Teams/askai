"""Bounded parallel startup work; progress callbacks run on the caller thread."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from askai.core.support.performance import timed


def run_startup_tasks(tasks, on_completed=lambda name: None):
    def run(name, action):
        with timed('startup.' + name):
            return action()

    results = {}
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix='askai-startup') as pool:
        futures = {pool.submit(run, name, action): name for name, action in tasks.items()}
        try:
            for future in as_completed(futures):
                name = futures[future]
                results[name] = future.result()
                on_completed(name)
        except BaseException:
            for future in futures:
                future.cancel()
            raise
    return results
