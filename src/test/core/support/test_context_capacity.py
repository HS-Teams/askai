"""Test context units without initializing application caches or devices."""
import ast
from collections import defaultdict, deque, namedtuple
from functools import partial, reduce
from pathlib import Path
import unittest
from typing import Literal, get_args
from unittest.mock import Mock


def context_class():
    source = Path(__file__).parents[3] / 'main/askai/core/support/chat_context.py'
    tree = ast.parse(source.read_text())
    tree.body = [ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)] + [
        item for item in tree.body if isinstance(item, ast.ClassDef)]
    namespace = dict(defaultdict=defaultdict, deque=deque, partial=partial, reduce=reduce,
                     ContextEntry=namedtuple('ContextEntry', 'role content recordable', defaults=[True]),
                     configs=Mock(is_keep_context=True),
                     ChatRoles=Literal['system', 'human', 'assistant'], get_args=get_args,
                     check_argument=Mock(), TokenLengthExceeded=ValueError)
    exec(compile(ast.fix_missing_locations(tree), str(source), 'exec'), namespace)
    return namespace['ChatContext']


class ContextCapacityTests(unittest.TestCase):
    def test_capacity_is_in_tokens_not_kilobytes(self):
        context = context_class()(2, 10)
        self.assertEqual(context.token_limit, 2)
        context.push('HISTORY', 'hello')
        with self.assertRaises(ValueError):
            context.push('HISTORY', 'word ' * 10)

    def test_unknown_capacity_keeps_history_bounded_by_entry_count(self):
        context = context_class()(None, 2)
        for content in ('one', 'two', 'three'):
            context.push('HISTORY', content)
        self.assertIsNone(context.token_limit)
        self.assertEqual(len(context.get('HISTORY')), 2)
