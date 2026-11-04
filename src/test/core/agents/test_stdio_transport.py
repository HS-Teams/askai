import sys
import unittest
from unittest.mock import Mock
from askai.core.agents.contracts import AgentError, AgentSessionNotFound
from askai.core.agents.stdio_transport import StdioTransport


class TransportTests(unittest.TestCase):
    def test_only_explicit_missing_rollout_is_classified_for_session_recovery(self):
        for method, error, missing in [
            ('thread/resume', {'code': -32600, 'message': 'no rollout found for thread id s'}, True),
            ('thread/archive', {'code': -32600, 'message': 'no rollout found for thread id s'}, True),
            ('thread/resume', {'code': -32600, 'message': 'invalid model'}, False),
            ('thread/resume', {'code': -32603, 'message': 'connection failed'}, False),
            ('thread/resume', {'code': -32600, 'message': 'no rollout found for thread id another'}, False),
            ('thread/resume', {'code': -32600, 'message': 'no rollout found for thread id s-other'}, False),
        ]:
            with self.subTest(method=method, error=error):
                transport = StdioTransport(['unused'])
                transport.send = Mock()
                transport._receive = Mock(return_value={'id': 1, 'error': error})
                with self.assertRaises(AgentError) as raised:
                    transport.request(method, {'threadId': 's'})
                self.assertEqual(isinstance(raised.exception, AgentSessionNotFound), missing)
    def test_interleaved_notification_is_preserved_and_process_is_reaped(self):
        script = """import json, sys
request=json.loads(sys.stdin.readline())
print(json.dumps({'method':'progress','params':{}}),flush=True)
print(json.dumps({'id':request['id'],'result':{'ok':True}}),flush=True)
sys.stdin.readline()
"""
        with StdioTransport([sys.executable, "-u", "-c", script]) as transport:
            self.assertEqual(transport.request("test", {}), {"ok": True})
            self.assertEqual(transport.receive()["method"], "progress")
        self.assertIsNotNone(transport._process.poll())

    def test_malformed_message_and_eof_raise_without_hanging(self):
        for script in ["print('not json',flush=True)", "pass"]:
            with self.subTest(script=script), self.assertRaises(AgentError):
                with StdioTransport(
                    [sys.executable, "-u", "-c", script], timeout=1
                ) as transport:
                    transport.request("test", {})

    def test_timeout_does_not_retry_request(self):
        with self.assertRaisesRegex(AgentError, "timed out"):
            with StdioTransport(
                [sys.executable, "-c", "import time; time.sleep(10)"], timeout=0.05
            ) as transport:
                transport.request("test", {})
