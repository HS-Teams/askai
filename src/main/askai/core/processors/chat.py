"""Taius conversation using native inference and AskAI's STM."""
from askai.core.askai_prompt import prompt
from askai.core.support.shared_instances import shared
from askai.core.model.refined_response import RefinedResponse
from askai.exception.exceptions import InaccurateResponse, TerminatingQuery
from pydantic import ValidationError


class ChatProcessor:
    def process(self, question: str, **kwargs) -> str:
        if not question:
            raise TerminatingQuery("The user wants to exit!")
        if question.casefold() in {"exit", "leave", "quit", "q"}:
            from askai.core.askai_events import events
            events.mode_changed.emit(mode="DEFAULT")
            return None
        template = prompt.read_prompt("taius-jarvis", prompt.append_path("taius"))
        instructions = template.format(user=prompt.user.title(), idiom=shared.idiom,
                                       context=kwargs.get("context") or "", question=question)
        messages = [{"role": "system", "content": instructions}]
        messages.extend(shared.context.messages("HISTORY"))
        if not messages or messages[-1] != {"role": "user", "content": question}:
            messages.append({"role": "user", "content": question})
        raw = shared.engine.complete(messages, schema=RefinedResponse.model_json_schema())
        try:
            return RefinedResponse.model_validate_json(raw).final_answer
        except (ValidationError, TypeError) as error:
            raise InaccurateResponse('Chat returned an invalid final-answer payload') from error


chat = ChatProcessor()
