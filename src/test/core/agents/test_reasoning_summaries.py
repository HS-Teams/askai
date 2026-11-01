import unittest
from askai.core.agents.reasoning_summaries import ReasoningSummaries


class SummaryTests(unittest.TestCase):
    def test_emits_readable_parts_before_completion_without_repeating_them(self):
        stream = ReasoningSummaries()
        self.assertEqual(stream.append('r', 0, 'Checking'), [])
        self.assertEqual(stream.append('r', 0, ' sources. Next'), ['Checking sources.'])
        self.assertEqual(stream.complete('r', ['Checking sources. Next step.']), ['Next step.'])
        self.assertEqual(stream.complete('r', ['Checking sources. Next step.']), [])

    def test_items_and_sections_are_independent(self):
        stream = ReasoningSummaries()
        self.assertEqual(stream.append('a', 0, 'First\n'), ['First'])
        self.assertEqual(stream.append('a', 1, 'Second\n'), ['Second'])
        self.assertEqual(stream.complete('b', ['Separate summary']), ['Separate summary'])
        self.assertEqual(stream.complete('a', ['First\n', 'Second\n']), [])
