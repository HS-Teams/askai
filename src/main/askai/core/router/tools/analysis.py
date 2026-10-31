#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.router.tools.analysis
      @file: analysis.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.ai_reply import AIReply
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import TextFormatter

import logging as log


def query_output(query: str, context: str = None) -> str:
    """Handle 'Text analysis', invoking: analyze(question: str). Analyze the context and answer the question.
    :param query: The question about the content to be analyzed.
    :param context: The context of the question.
    """
    context = context or shared.context.flat("HISTORY")
    output = shared.engine.complete([
        {"role": "system", "content": prompt.read_prompt("analysis")},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}], Temperature.DATA_ANALYSIS.temp)
    return TextFormatter.ensure_ln(output)
