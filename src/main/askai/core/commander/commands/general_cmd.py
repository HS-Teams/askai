#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.general_cmd
      @file: general_cmd.py
   @created: Mon, 06 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from abc import ABC
from askai.core.askai_messages import AskAiMessages
from askai.core.askai_settings import settings
from askai.core.component.summarizer import summarizer
from askai.core.support.shared_instances import shared
from askai.cli import output as cli_output
from askai.language.language import Language
from clitt.core.term.terminal import Terminal
from hspylib.core.config.path_object import PathObject
from hspylib.modules.application.exit_status import ExitStatus

import locale
import os.path


class GeneralCmd(ABC):
    """Provides general command functionalities."""

    @staticmethod
    def app_info() -> None:
        """Display some useful application information."""
        cli_output.render_text(shared.app_info)

    @staticmethod
    def execute(cmd_line: str | None = None) -> None:
        """Execute a terminal command.
        :param cmd_line: The command line to execute (optional).
        """
        output, err_out, exit_code = Terminal.INSTANCE.shell_exec(cmd_line, shell=True)
        if exit_code == ExitStatus.SUCCESS:
            cli_output.render_command(output)
        else:
            cli_output.render_message(f"\nCommand `{cmd_line}` failed. Error({err_out})  Code ({exit_code})")

    @staticmethod
    def summarize(folder: str, glob: str) -> None:
        """Generate a summarization of files and folder contents.
        :param folder: The base folder from which the summarization will be generated.
        :param glob: The glob pattern specifying which files or folders to include in the summarization.
        """
        sum_dir: PathObject | None = PathObject.of(folder)
        if sum_dir and os.path.exists(sum_dir.abs_dir):
            if summarizer.generate(sum_dir.abs_dir, glob):
                cli_output.render_command(f"Summarization complete. Folder: *{folder}*  Glob: *{glob}* !")
            else:
                cli_output.render_message(f"\n-=- Failed to summarize. Folder: {folder}  Glob: {glob} ! -=-")
        else:
            cli_output.render_message(f"\n-=- Folder '{folder}' does not exist! -=-")

    @staticmethod
    def idiom(locale_str: str) -> None:
        """Set the application language.
        :param locale_str: The locale string.
        """
        try:
            if locale_str and (language := Language.of_locale(locale_str)):
                locale.setlocale(locale.LC_ALL, (language.idiom, language.encoding.val))
                settings.put("askai.preferred.language", language.idiom)
                cli_output.render_command(f"Locale changed to: {language}")
            else:
                current_locale = locale.getlocale(locale.LC_ALL)
                loc_str = f"{current_locale[0]}.{current_locale[1]}" if all(current_locale) else ""
                language = Language.of_locale(loc_str)
                cli_output.render_command(f"Current locale: {language}")
        except (ValueError, TypeError) as err:
            cli_output.render_message(f"\n-=- Failed to set idiom: '{str(err)}'! -=-")

    @staticmethod
    def translate(from_lang: Language, *texts: str) -> None:
        """Translate text from the source language to the target language.
        :param from_lang: The source language.
        :param texts: The texts to be translated.
        """
        translator = AskAiMessages.get_translator(from_lang)
        list(map(cli_output.render_message, map(translator.translate, texts)))
