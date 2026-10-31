import sys
import unittest
from askai.core.agents.contracts import AgentError
from askai.core.agents.stdio_transport import StdioTransport


class TransportTests(unittest.TestCase):
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
