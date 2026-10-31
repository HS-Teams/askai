#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.router.tools.generation
      @file: generation.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""

from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import GEN_AI_DIR
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import extract_codeblock
from hspylib.core.config.path_object import PathObject
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.preconditions import check_not_none
from hspylib.core.zoned_datetime import now_ms
from pathlib import Path
from typing import AnyStr

import logging as log
from askai.core.support.inference import complete
import os


def generate_content(instructions: str, mime_type: str, filepath: AnyPath | None = None) -> str:
    """Generate content using the AI. It's a general function now, but it can be specialized afterwards.
    :param instructions: The instructions for generating the content.
    :param mime_type: The generated content type (use MIME types).
    :param filepath: Optional file path for saving the content.
    """
    check_not_none((instructions, mime_type))
    template = prompt.read_prompt("generator")
    final_prompt: str = template.format(mime_type=mime_type, input=instructions)
    instructions += "\nFormat the content into a markdown code block.\n"

    log.info("GENERATE::[PROMPT] '%s'  Type: '%s'", instructions, mime_type)
    response = complete(final_prompt, Temperature.CODE_GENERATION.temp)
    timestamp: int = now_ms()
    final_path: str = str(filepath or f"{GEN_AI_DIR}/gen-ai-{timestamp}")

    if response and (output := response):
        shared.context.set("GENERATED", output)
        save_content(final_path)
    else:
        output = msg.no_output("GenAI")

    return f"The following file: *{final_path}* (`{mime_type}`) was generated. Contents:\n\n{output}\n"


def save_content(filepath: AnyPath, content: AnyStr | None = None) -> str:
    """Save any generated context into a file.
    :param filepath: The path where you want to save the content.
    :param content: Optional content to be saved. If not provided, it will get from the last generated context.
    """
    if filepath:
        path_obj = PathObject.of(filepath)
        base_dir = path_obj.abs_dir
        if Path(base_dir).exists and (output := str(content or shared.context.flat("GENERATED"))):
            filename: str = path_obj.join()
            with open(filename, "w") as f_path_name:
                lang, content = extract_codeblock(output)
                f_path_name.write(f"\n{content}\n")
                output = f"{lang.title() if lang else 'The '} content was successfully saved as: '{filename}'\n"
        if not os.path.exists(filepath):
            output = f"Sorry, the AI was unable save the content at: '{filepath}' !"
    else:
        output = f"File path '{filepath}' was not found !"

    return output
