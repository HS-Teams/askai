import unittest
from askai.cli.suggestions import input_suggestion


class SuggestionTests(unittest.TestCase):
    def setUp(self):
        self.entries = ['/gestures --help', '/history list', '/session reset',
                        '/gestures', '/history', '/session', 'hello world']

    def test_pure_command_wins_even_when_help_or_history_appears_first(self):
        for prefix, expected in [('/g', '/gestures'), ('/gestures', '/gestures'),
                                 ('/hist', '/history'), ('/ses', '/session')]:
            self.assertEqual(input_suggestion(prefix, self.entries), expected)

    def test_space_enables_options_and_subcommands(self):
        for prefix, expected in [('/gestures ', '/gestures --help'),
                                 ('/gestures --h', '/gestures --help'),
                                 ('/history ', '/history list'), ('/session r', '/session reset')]:
            self.assertEqual(input_suggestion(prefix, self.entries), expected)

    def test_case_insensitive_and_regular_text_completion(self):
        self.assertEqual(input_suggestion('/GES', self.entries, False), '/gestures')
        self.assertIsNone(input_suggestion('/GES', self.entries))
        self.assertEqual(input_suggestion('hello', self.entries), 'hello world')
        self.assertIsNone(input_suggestion('/unknown', self.entries))

    def test_exact_command_is_not_extended_to_another_command(self):
        self.assertEqual(input_suggestion('/history', ['/history-extra --help', '/history list']), '/history')
