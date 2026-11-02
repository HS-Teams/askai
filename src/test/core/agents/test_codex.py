import unittest
from pathlib import Path
from threading import Event
from unittest.mock import Mock, patch

from askai.core.agents.codex import CodexBackend
from askai.core.agents.contracts import AgentTask, AgentError


class CodexTests(unittest.TestCase):
    def test_computer_tool_title_is_forwarded_as_progress(self):
        transport = self.transport([
            {'method': 'item/started', 'params': {'item': {'type': 'mcpToolCall',
             'arguments': {'title': 'Check reminder details'}}}},
            {'method': 'item/completed', 'params': {'item': {'type': 'agentMessage',
             'id': 'a', 'phase': 'final_answer', 'text': 'Unable to save; partial item remains.'}}},
            {'method': 'turn/completed', 'params': {'turn': {'id': 't', 'status': 'completed'}}},
        ])
        emit = Mock()
        CodexBackend(transport_factory=lambda _: transport).run(
            AgentTask('create reminder', Path.cwd()), emit, Mock(), Event())
        progress = [c.args[0].data['message'] for c in emit.call_args_list if c.args[0].kind == 'tool_progress']
        self.assertIn('Check reminder details', progress)


    def test_writes_require_escalation_for_new_resumed_and_private_turns(self):
        for session in (None, 's'):
            for history in (True, False):
                for read_only in (False, True):
                    with self.subTest(session=session, history=history, read_only=read_only):
                        transport = self.transport([])
                        backend = CodexBackend(transport_factory=lambda _: transport)
                        with patch.object(backend, '_consume', return_value=Mock()):
                            if session and not history:
                                backend.run(AgentTask('start', Path.cwd(), persist_history=False),
                                            Mock(), Mock(), Event())
                                transport.request.reset_mock()
                            backend.run(AgentTask('remove selected files', Path.cwd(), session_id=session,
                                                  persist_history=history, read_only=read_only),
                                        Mock(), Mock(), Event())
                        for call in transport.request.call_args_list:
                            method, options = call.args
                            if method in ('thread/start', 'thread/resume'):
                                self.assertEqual(options['sandbox'], 'read-only')
                            if method == 'turn/start':
                                self.assertEqual(options['sandboxPolicy'], {'type': 'readOnly'})
                                self.assertEqual(options['approvalPolicy'], 'never' if read_only else 'on-request')

    def test_file_deletion_approval_denial_is_returned_to_codex(self):
        transport = Mock()
        interact = Mock(return_value={'decision': 'decline'})
        request = {'id': 42, 'method': 'item/commandExecution/requestApproval',
                   'params': {'command': 'rm /example/selected-file'}}
        CodexBackend._respond(transport, request, interact)
        interact.assert_called_once_with(request['method'], request['params'])
        transport.send.assert_called_once_with({'id': 42, 'result': {'decision': 'decline'}})


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
                    "params": {"item": {"type": "reasoning", "text": "private",
                                        "content": ["raw private"], "summary": ["Checking sources."]}},
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
                    "method": "item/completed",
                    "params": {"item": {"type": "agentMessage", "id": "later",
                                        "phase": "commentary", "text": "Later update"}},
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
        backend = CodexBackend(transport_factory=lambda command: transport, debug=lambda: True)
        events = []
        result = backend.run(
            AgentTask("Inspect", Path.cwd()),
            events.append,
            lambda method, params: {"decision": "decline"},
            Event(),
        )
        self.assertEqual(result.answer, "Done")
        self.assertEqual(events[1].data, {"text": "Checking sources."})
        self.assertEqual(events[2].data, {"text": "working"})
        self.assertEqual([e.kind for e in events], ["started", "reasoning_summary", "initial_commentary", "completed"])
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
        self.assertEqual(turn["summary"], "auto")

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

    def test_archive_uses_protocol_without_starting_a_turn(self):
        transport = self.transport([])
        transport.request.side_effect = None
        transport.request.return_value = {'account': {'type': 'chatgpt'}}
        backend = CodexBackend(transport_factory=Mock(return_value=transport))
        self.addCleanup(backend.close)
        backend.archive('previous')
        transport.request.assert_any_call('thread/archive', {'threadId': 'previous'})
        self.assertNotIn('turn/start', [c.args[0] for c in transport.request.call_args_list])

    def test_private_session_has_no_persisted_thread_to_archive(self):
        factory = Mock()
        backend = CodexBackend(transport_factory=factory)
        backend._private_sessions.add('private')
        backend.archive('private')
        factory.assert_not_called()
