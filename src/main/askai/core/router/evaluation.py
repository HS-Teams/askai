#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.router.evaluation
      @file: analysis.py
   @created: Fri, 03 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""

from askai.core.askai_prompt import prompt
from askai.core.component.rag_provider import RAGProvider
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.acc_response import AccResponse
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse
from textwrap import dedent


# fmt: off
EVALUATION_GUIDE: str = dedent("""
**Accuracy Evaluation Guidelines:**

1. Analyze past responses to ensure accuracy.
2. Regularly self-critique overall responses.
3. Reflect on past strategies to refine your approach.
4. Experiment with different methods or solutions.
""").strip()
# fmt: on

RAG: RAGProvider = RAGProvider("accuracy.csv")


def eval_response(question: str, ai_response: str) -> AccResponse:
    """Check whether the AI's response to the question meets the required accuracy.
    :param question: The user's question.
    :param ai_response: The AI's response to be analyzed for accuracy.
    :return: The accuracy classification of the AI's response as an AccResponse enum value.
    """
    from askai.core.component.answer_validator import validate_response

    if not ai_response:
        raise InaccurateResponse("Accuracy response was empty")
    return validate_response(shared.engine, prompt.read_prompt("evaluation"),
                             rag=RAG.get_rag_examples(question) or "", input=question, response=ai_response)


def resolve_x_refs(ref_name: str, context: str | None = None) -> str:
    """Replace all cross-references with their actual values.
    :param ref_name: The name of the cross-reference or variable to resolve.
    :param context: The context in which to analyze and resolve the references (optional).
    :return: The string with all cross-references replaced by their corresponding values.
    """
    messages = [{"role": "system", "content": prompt.read_prompt("x-references")}]
    if context:
        messages.append({"role": "user", "content": context})
    else:
        messages.extend(shared.context.messages("HISTORY"))
    messages.append({"role": "user", "content": ref_name})
    return shared.engine.complete(messages, Temperature.CODE_GENERATION.temp)
