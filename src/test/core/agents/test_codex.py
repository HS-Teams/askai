import unittest
from pathlib import Path
from threading import Event
from unittest.mock import Mock

from askai.core.agents.codex import CodexBackend
from askai.core.agents.contracts import AgentTask, AgentError


class CodexTests(unittest.TestCase):
    def transport(self, notifications):
        transport = Mock()
        transport.__enter__ = Mock(return_value=transport)
        transport.__exit__ = Mock(return_value=False)
        results = {
            "initialize": {},
            "account/read": {"account": {"type": "chatgpt"}},
            "thread/start": {"thread": {"id": "s"}},
            "thread/name/set": {},
            "thread/unsubscribe": {},
            "thread/resume": {"thread": {"id": "s"}},
            "turn/start": {"turn": {"id": "t"}},
            "turn/interrupt": {},
        }
        transport.request.side_effect = lambda method, params: results[method]
        transport.receive.side_effect = notifications
        return transport

    def test_final_answer_excludes_commentary_and_reasoning_and_handles_approval(self):
        transport = self.transport(
            [
                {
                    "method": "item/completed",
                    "params": {"item": {"type": "reasoning", "text": "private"}},
                },
                {
                    "method": "item/completed",
                    "params": {
                        "item": {
                            "type": "agentMessage",
                            "id": "a",
                            "phase": "commentary",
                            "text": "working",
                        }
                    },
                },
                {
                    "id": 99,
                    "method": "item/commandExecution/requestApproval",
                    "params": {"command": "pwd"},
                },
                {
                    "method": "item/completed",
                    "params": {
                        "item": {
                            "type": "agentMessage",
                            "id": "b",
                            "phase": "final_answer",
                            "text": "Done",
                        }
                    },
                },
                {
                    "method": "turn/completed",
                    "params": {"turn": {"id": "t", "status": "completed"}},
                },
            ]
        )
        backend = CodexBackend(transport_factory=lambda command: transport)
        events = []
        result = backend.run(
            AgentTask("Inspect", Path.cwd()),
            events.append,
            lambda method, params: {"decision": "decline"},
            Event(),
        )
        self.assertEqual(result.answer, "Done")
        self.assertEqual([e.kind for e in events], ["started", "completed"])
        transport.send.assert_any_call({"id": 99, "result": {"decision": "decline"}})
        transport.__exit__.assert_not_called()
        backend.close()
        transport.__exit__.assert_called_once()
        options = next(
            call.args[1]
            for call in transport.request.call_args_list
            if call.args[0] == "thread/start"
        )
        self.assertIn("askai_desktop MCP play_music", options["developerInstructions"])
        self.assertIn("Do not launch afplay", options["developerInstructions"])

        turn = next(
            call.args[1]
            for call in transport.request.call_args_list
            if call.args[0] == "turn/start"
        )
        self.assertEqual(turn["effort"], "low")

    def test_cancel_is_confirmed_by_terminal_event(self):
        transport = self.transport(
            [
                {
                    "method": "turn/completed",
                    "params": {"turn": {"id": "t", "status": "interrupted"}},
                }
            ]
        )
        cancelled = Event()
        result = CodexBackend(transport_factory=lambda _: transport).run(
            AgentTask("Inspect", Path.cwd(), session_id="s"),
            lambda event: cancelled.set(),
            Mock(),
            cancelled,
        )
        self.assertEqual(result.status, "interrupted")
        transport.request.assert_any_call(
            "turn/interrupt", {"threadId": "s", "turnId": "t"}
        )
        self.assertIn(
            "thread/resume", [c.args[0] for c in transport.request.call_args_list]
        )

    def test_missing_final_answer_and_failed_turn_are_errors(self):
        for status in ["completed", "failed"]:
            with self.subTest(status=status), self.assertRaises(AgentError):
                transport = self.transport(
                    [
                        {
                            "method": "turn/completed",
                            "params": {"turn": {"id": "t", "status": status}},
                        }
                    ]
                )
                CodexBackend(transport_factory=lambda _: transport).run(
                    AgentTask("Inspect", Path.cwd()), Mock(), Mock(), Event()
                )

    def test_unknown_request_is_rejected_not_approved(self):
        transport = self.transport(
            [{"id": 42, "method": "unknown/request", "params": {}}]
        )
        handler = Mock()
        with self.assertRaisesRegex(AgentError, "unsupported"):
            CodexBackend(transport_factory=lambda _: transport).run(
                AgentTask("Inspect", Path.cwd()), Mock(), handler, Event()
            )
        handler.assert_not_called()
        self.assertEqual(transport.send.call_args.args[0]["error"]["code"], -32601)

    def test_cancelled_request_never_starts_process(self):
        cancelled = Event()
        cancelled.set()
        factory = Mock()
        with self.assertRaisesRegex(AgentError, "cancelled before"):
            CodexBackend(transport_factory=factory).run(
                AgentTask("Inspect", Path.cwd()), Mock(), Mock(), cancelled
            )
        factory.assert_not_called()


class DailySessionTests(unittest.TestCase):
    transport = CodexTests.transport

    def test_new_session_is_named_and_receives_tools_only_once(self):
        for session_id in (None, "s"):
            with self.subTest(session_id=session_id):
                transport = self.transport(
                    [
                        {
                            "method": "item/completed",
                            "params": {
                                "item": {
                                    "type": "agentMessage",
                                    "phase": "final_answer",
                                    "id": "a",
                                    "text": "Done",
                                }
                            },
                        },
                        {
                            "method": "turn/completed",
                            "params": {"turn": {"id": "t", "status": "completed"}},
                        },
                    ]
                )
                CodexBackend(transport_factory=lambda _: transport).run(
                    AgentTask(
                        "hello",
                        Path.cwd(),
                        session_id=session_id,
                        session_name="2026-10-31",
                    ),
                    Mock(),
                    Mock(),
                    Event(),
                )
                method = "thread/resume" if session_id else "thread/start"
                options = next(
                    call.args[1]
                    for call in transport.request.call_args_list
                    if call.args[0] == method
                )
                names = [
                    call
                    for call in transport.request.call_args_list
                    if call.args[0] == "thread/name/set"
                ]
                if session_id:
                    self.assertFalse(names)
                    self.assertNotIn("This is a new", options["developerInstructions"])
                else:
                    self.assertEqual(
                        names[0].args[1], {"threadId": "s", "name": "2026-10-31"}
                    )
                    for tool in (
                        "open_path",
                        "open_application",
                        "play_music",
                        "control_music",
                        "open_camera",
                        "capture_camera",
                    ):
                        self.assertIn(tool + "(", options["developerInstructions"])
