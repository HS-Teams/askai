from threading import Barrier, get_ident
import unittest
from askai.core.support.startup import run_startup_tasks


class StartupTests(unittest.TestCase):
    def test_independent_tasks_overlap_and_progress_stays_on_caller(self):
        barrier = Barrier(3)
        caller = get_ident()
        callbacks = []
        def task():
            barrier.wait(timeout=2)
            return get_ident()
        results = run_startup_tasks({str(i): task for i in range(3)},
                                    lambda name: callbacks.append((name, get_ident())))
        self.assertEqual(len(set(results.values())), 3)
        self.assertTrue(all(thread == caller for _, thread in callbacks))
        self.assertEqual({name for name, _ in callbacks}, set(results))

    def test_failed_initialization_is_reported(self):
        def fail():
            raise ValueError('failed startup')
        with self.assertRaisesRegex(ValueError, 'failed startup'):
            run_startup_tasks({'failure': fail})
