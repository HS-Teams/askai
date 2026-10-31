import unittest
from textual import work
from textual.app import App
from askai.tui.agent_interaction import AgentInteraction


class DialogApp(App):
    def __init__(self, method, params):
        super().__init__()
        self.method, self.params, self.result = method, params, None

    def on_mount(self):
        self.ask()

    @work(thread=True)
    def ask(self):
        self.result = self.call_from_thread(
            self.push_screen_wait, AgentInteraction(self.method, self.params)
        )


class InteractionTests(unittest.IsolatedAsyncioTestCase):
    async def test_approval_from_worker_has_explicit_accept_and_deny(self):
        for button, decision in [("allow", "accept"), ("deny", "decline")]:
            app = DialogApp("item/commandExecution/requestApproval", {"command": "pwd"})
            async with app.run_test(size=(100, 40)) as pilot:
                await pilot.pause()
                await pilot.click("#" + button)
                await pilot.pause()
                self.assertEqual(app.result, {"decision": decision})

    async def test_user_answer_is_correlated_by_question_id(self):
        app = DialogApp(
            "item/tool/requestUserInput",
            {"questions": [{"id": "q1", "question": "Which file?"}]},
        )
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#answer-0")
            await pilot.press("a", ".", "p", "y")
            await pilot.click("#send")
            await pilot.pause()
            self.assertEqual(app.result, {"answers": {"q1": {"answers": ["a.py"]}}})

    async def test_mcp_form_returns_typed_content(self):
        app = DialogApp('mcpServer/elicitation/request', {
            'mode': 'form', 'message': 'Quantidade?', 'requestedSchema': {
                'type': 'object', 'properties': {'count': {'type': 'integer', 'minimum': 1}},
                'required': ['count']}})
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            await pilot.click('#field-0')
            await pilot.press('2')
            await pilot.click('#elicit-send')
            await pilot.pause()
            self.assertEqual(app.result, {'action': 'accept', 'content': {'count': 2}})
