"""Human interaction through AskAI's input and presentation adapters."""

import getpass
import logging
import sys
from jsonschema import ValidationError
from askai.core.agents.elicitation import (
    ELICITATION_METHOD,
    INPUT_FORM_METHOD,
    FORM_MODES,
    decode_form,
    field_label,
)
from askai.core.agents.contracts import AgentError
from askai.cli.confirmation import Confirmation
from askai.cli.interaction_text import translate_request


def approval_message(params: dict, translate=lambda text: text) -> str:
    lines = [
        params.get("reason")
        or translate("Your permission is needed to continue this action.")
    ]
    if command := params.get("command"):
        lines.append(translate("Requested command:") + f" {command}")
    elif changes := params.get("changes"):
        lines.append(translate("Affected files:") + ", ".join(changes))
    if cwd := params.get("cwd"):
        lines.append(translate("Working directory:") + f" {cwd}")
    return "\n".join(lines)


def deny_decision(params: dict) -> dict:
    available = params.get("availableDecisions")
    return {
        "decision": (
            "decline" if available is None or "decline" in available else "cancel"
        )
    }


class AgentInteraction:
    def __init__(
        self,
        read,
        show,
        read_secret=getpass.getpass,
        confirm=None,
        translate=lambda text: text,
    ):
        self._read, self._show, self._read_secret = read, show, read_secret
        self._confirm = confirm or Confirmation(read, show, translate)
        self._translate = translate

    def __call__(self, method: str, params: dict) -> dict:
        if not sys.stdin.isatty():
            raise AgentError(
                self._translate(
                    "This action requires a response in an interactive AskAI session."
                )
            )
        # Protocol diagnostics belong in logs, never in the conversation.
        logging.debug(
            "Agent interaction method=%s item=%s", method, params.get("itemId")
        )
        params = translate_request(params, self._translate)
        if method in {ELICITATION_METHOD, INPUT_FORM_METHOD}:
            return self._elicit(params, confirm=method == ELICITATION_METHOD)
        if method == "item/tool/requestUserInput":
            answers = {}
            for question in params.get("questions", []):
                self._show(question["question"])
                for option in question.get("options") or []:
                    self._show(f"{option['label']}: {option.get('description', '')}")
                value = (
                    self._read_secret(self._translate("Protected answer: "))
                    if question.get("isSecret")
                    else self._read(self._translate("Your answer"))
                )
                if not value:
                    return {"answers": {}}
                answers[question["id"]] = {"answers": [value]}
            return {"answers": answers}
        if method == "item/permissions/requestApproval":
            self._show(
                self._translate(
                    "This additional permission type is not supported yet. The request was denied."
                )
            )
            return {"permissions": {}}
        if self._confirm(approval_message(params, self._translate)):
            return {"decision": "accept"}
        return deny_decision(params)

    def _elicit(self, params, *, confirm=True):
        mode = params.get("mode", "form")
        message = f"{params.get('serverName') or self._translate('Tool')}: {params.get('message', '')}"
        if mode == "url":
            self._show(message + "\n" + params["url"])
            accepted = self._confirm(
                self._translate(
                    "Have you completed the step at the address above and want to continue?"
                )
            )
            return {"action": "accept" if accepted else "decline"}
        if mode not in FORM_MODES:
            self._show(
                self._translate(
                    "This request format is not supported yet. Request cancelled."
                )
            )
            return {"action": "cancel"}
        if confirm and not self._confirm(message):
            return {"action": "decline"}
        if not confirm:
            self._show(message)
        schema = params["requestedSchema"]
        while True:
            values = {}
            for name, field in schema.get("properties", {}).items():
                self._show(field_label(name, field, self._translate))
                value = (
                    self._read_secret(self._translate("Protected answer: "))
                    if field.get("format") == "password"
                    else self._read(self._translate("Answer (/cancel to cancel)"))
                )
                if value is None or value.strip().casefold() in {
                    "/cancel",
                    "/cancelar",
                }:
                    return {"action": "cancel"}
                values[name] = value
            try:
                return {"action": "accept", "content": decode_form(schema, values)}
            except (ValueError, ValidationError) as error:
                self._show(
                    self._translate("Invalid answer:")
                    + " "
                    + self._translate(
                        error.message
                        if isinstance(error, ValidationError)
                        else str(error)
                    )
                )
