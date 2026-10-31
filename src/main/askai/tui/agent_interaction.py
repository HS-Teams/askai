"""View-owned dialogs for specialized-agent approvals and questions."""

from askai.cli.agent_interaction import approval_message, deny_decision
from askai.cli.interaction_text import translate_request
from jsonschema import ValidationError
from askai.core.agents.elicitation import (
    ELICITATION_METHOD,
    FORM_MODES,
    field_label,
    decode_form,
)
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import VerticalScroll
from textual.widgets import Button, Input, Static


class AgentInteraction(ModalScreen[dict]):
    BINDINGS = [("escape", "deny", "Cancel")]

    def __init__(self, method: str, params: dict, translate=lambda text: text):
        super().__init__()
        self._translate = translate
        self.method, self.params = method, translate_request(params, translate)

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            if self.method == ELICITATION_METHOD:
                yield Static(
                    f"{self.params.get('serverName') or self._translate('Tool')}: {self.params.get('message', '')}",
                    markup=False,
                )
                mode = self.params.get("mode", "form")
                if mode == "url":
                    yield Static(self.params["url"], markup=False)
                    yield Button(
                        self._translate("Step completed, continue"),
                        id="elicit-url",
                        variant="primary",
                    )
                elif mode in FORM_MODES:
                    for index, (name, field) in enumerate(
                        self.params["requestedSchema"].get("properties", {}).items()
                    ):
                        yield Static(
                            field_label(name, field, self._translate), markup=False
                        )
                        yield Input(
                            id=f"field-{index}",
                            password=field.get("format") == "password",
                        )
                    yield Static("", id="form-error", markup=False)
                    yield Button(
                        self._translate("Confirm and send"),
                        id="elicit-send",
                        variant="primary",
                    )
                else:
                    yield Static(
                        self._translate("Unsupported format. Cancel this request."),
                        markup=False,
                    )
            elif self.method == "item/tool/requestUserInput":
                for index, question in enumerate(self.params.get("questions", [])):
                    yield Static(question["question"], markup=False)
                    for option in question.get("options") or []:
                        yield Static(
                            f"{option['label']}: {option.get('description', '')}",
                            markup=False,
                        )
                    yield Input(
                        id=f"answer-{index}", password=question.get("isSecret", False)
                    )
                yield Button(
                    self._translate("Send answers"), id="send", variant="primary"
                )
            else:
                yield Static(
                    self._translate("Permission for this action"), markup=False
                )
                yield Static(
                    approval_message(self.params, self._translate), markup=False
                )
                if self.method != "item/permissions/requestApproval":
                    yield Button(
                        self._translate("Allow this action"),
                        id="allow",
                        variant="primary",
                    )
                else:
                    yield Static(
                        self._translate(
                            "This additional permission type is not supported yet."
                        ),
                        markup=False,
                    )
            yield Button(self._translate("Deny / cancel"), id="deny")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "elicit-url":
            self.dismiss({"action": "accept"})
        elif event.button.id == "elicit-send":
            schema = self.params["requestedSchema"]
            values = {
                name: self.query_one(f"#field-{i}", Input).value
                for i, name in enumerate(schema.get("properties", {}))
            }
            try:
                content = decode_form(schema, values)
            except (ValueError, ValidationError) as error:
                self.query_one("#form-error", Static).update(
                    self._translate(
                        error.message
                        if isinstance(error, ValidationError)
                        else str(error)
                    )
                )
                return
            self.dismiss({"action": "accept", "content": content})
        elif event.button.id == "allow":
            self.dismiss({"decision": "accept"})
        elif event.button.id == "send":
            self.dismiss(
                {
                    "answers": {
                        question["id"]: {
                            "answers": [self.query_one(f"#answer-{i}", Input).value]
                        }
                        for i, question in enumerate(self.params.get("questions", []))
                    }
                }
            )
        else:
            self.action_deny()

    def action_deny(self):
        if self.method == ELICITATION_METHOD:
            self.dismiss({"action": "cancel"})
        elif self.method == "item/tool/requestUserInput":
            self.dismiss({"answers": {}})
        elif self.method == "item/permissions/requestApproval":
            self.dismiss({"permissions": {}})
        else:
            self.dismiss(deny_decision(self.params))
