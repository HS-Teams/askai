"""List parsing is still used by retained search and vision helpers."""
import unittest
from askai.core.support.llm_parser import parse_list


class ListParserTests(unittest.TestCase):
    def test_objects_and_strings_keep_their_content(self):
        tasks = parse_list('@tasks', '@tasks: [{"id": 1, "task": "List files"}]')
        self.assertEqual(tasks[0].task, 'List files')
        self.assertEqual(parse_list('@items', '@items: ["one", "two"]', is_dict=False), ['one', 'two'])
