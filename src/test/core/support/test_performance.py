import unittest
from unittest.mock import patch

from askai.core.support.performance import request_timing, timed


class PerformanceTests(unittest.TestCase):
    def test_elapsed_time_and_failure_are_logged_without_error_details(self):
        with patch('askai.core.support.performance.perf_counter', side_effect=[10, 12.5]):
            with self.assertLogs(level='INFO') as logs:
                with self.assertRaisesRegex(ValueError, 'private content'), timed('execution'):
                    raise ValueError('private content')
        self.assertIn('execution: 2.500s request=- outcome=failed', logs.output[0])
        self.assertNotIn('private content', logs.output[0])

    def test_request_ids_group_stages_and_reset_after_failure(self):
        with self.assertLogs(level='INFO') as logs:
            with self.assertRaises(ValueError), request_timing():
                with timed('execution'):
                    pass
                raise ValueError('failed')
            with request_timing(), timed('execution'):
                pass
            with timed('startup'):
                pass
        ids = [entry.split('request=')[1].split()[0] for entry in logs.output]
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(ids[2], ids[3])
        self.assertNotEqual(ids[0], ids[2])
        self.assertEqual(ids[4], '-')
