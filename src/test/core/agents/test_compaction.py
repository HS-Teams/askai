from pathlib import Path
import unittest
from unittest.mock import Mock
from askai.core.agents.compaction import compact_thread
from askai.core.agents.contracts import AgentError


def notification(method, **params):
    return {'method': method, 'params': {'threadId': 's', **params}}


class CompactionTests(unittest.TestCase):
    def test_acknowledgement_requires_compaction_item_and_completed_turn(self):
        transport = Mock()
        transport.receive.side_effect = [
            notification('turn/started', turn={'id': 'compact'}),
            notification('item/completed', turnId='compact', item={'type': 'contextCompaction', 'id': 'c'}),
            notification('turn/completed', turn={'id': 'other', 'status': 'completed'}),
            notification('turn/completed', turn={'id': 'compact', 'status': 'completed'}),
        ]
        compact_thread(transport, 's', Path.cwd())
        transport.request.assert_any_call('thread/compact/start', {'threadId': 's'})
        self.assertEqual(transport.receive.call_count, 4)

    def test_empty_acknowledgement_is_not_success(self):
        transport = Mock()
        transport.receive.return_value = None
        with self.assertRaisesRegex(AgentError, 'timed out'):
            compact_thread(transport, 's', Path.cwd(), timeout=.001)

    def test_failed_interrupted_and_missing_compaction_are_errors(self):
        for status in ('failed', 'interrupted', 'completed'):
            transport = Mock()
            transport.receive.side_effect = [notification('turn/completed', turn={'id': 't', 'status': status})]
            with self.subTest(status=status), self.assertRaises(AgentError):
                compact_thread(transport, 's', Path.cwd())

    def test_tool_interaction_is_rejected(self):
        transport = Mock()
        transport.receive.return_value = {'id': 42, **notification('item/tool/requestUserInput')}
        with self.assertRaisesRegex(AgentError, 'Unexpected interaction'):
            compact_thread(transport, 's', Path.cwd())
        self.assertEqual(transport.send.call_args.args[0]['error']['code'], -32601)
