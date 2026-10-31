#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.history_cmd
      @file: general_cmd.py
   @created: Sat, 22 Jun 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from abc import ABC
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text
from clitt.core.tui.line_input.keyboard_input import KeyboardInput
from textwrap import indent
from typing import Optional

import os
import pyperclip
import re


class HistoryCmd(ABC):
    """Provides history command functionalities."""

    @staticmethod
    def context_list() -> None:
        """List the entries in the chat context window."""

        if (all_context := shared.context) and (length := len(all_context)) > 0:
            ln: str = os.linesep
            display_text(f"### Listing ALL ({length}) Chat Contexts:\n\n---\n\n")
            for c in all_context:
                ctx, ctx_val = c[0], c[1]
                display_text(
                    f"- {ctx} ({len(ctx_val)}/{all_context.max_context_size} "
                    f"tk [{all_context.length(ctx)}/{all_context.token_limit}]) \n"
                    + indent(
                        ln.join(
                            [
                                f'{i}. **{e.role.title()}:**\n\n{indent(text_formatter.strip_format(e.content), " " * 4)}'
                                + os.linesep
                                for i, e in enumerate(ctx_val, start=1)
                            ]
                        ),
                        " " * 4,
                    ),
                    markdown=False,
                )
            display_text(f"> Hint: Type: '/context forget [context] to forget a it.")
        else:
            text_formatter.commander_print(f"%YELLOW% Context is empty %NC%")

    @staticmethod
    def context_forget(context: str | None = None) -> None:
        """Forget entries pushed to the chat context.
        :param context: The context key to forget, or None to forget all context entries.
        """
        if context := context if context != "ALL" else None:
            shared.context.clear(*(re.split(r"[;,|]", context.upper())))
        else:
            shared.context.forget()  # Clear the context
            shared.memory.clear()  # Also clear the chat memory
        text_formatter.commander_print(
            f"Context %GREEN%'{context.upper() if context else 'ALL'}'%NC% has been cleared!"
        )

    @staticmethod
    def context_copy(name: str | None = None) -> Optional[str]:
        """Copy a context entry to the clipboard.
        :param name: The name of the context entry to copy. If None, the default context will be copied.
        """
        copied_text: str | None = None
        if (name := name.upper()) in shared.context.keys:
            if (ctx := str(shared.context.flat(name.upper()))) and (
                copied_text := re.sub(
                    r"^((system|human|AI|assistant):\s*)", "", ctx, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE
                )
            ):
                pyperclip.copy(copied_text)
                text_formatter.commander_print(f"`{name}` copied to the clipboard!")
            else:
                text_formatter.commander_print(f"There is nothing to copy from `{name}`!")
        else:
            text_formatter.commander_print(f"Context name not found: `{name}`!")

        return copied_text

    @staticmethod
    def history_list(day: str | None = None) -> None:
        """List durable conversations for this agent and working directory."""
        from pathlib import Path
        from askai.core.askai_configs import configs
        from askai.core.askai_messages import msg
        from askai.core.askai_settings import ASKAI_DIR
        from askai.core.support.persistent_memory import PersistentMemory

        history = PersistentMemory(Path(ASKAI_DIR) / "memory" / "history.sqlite3")
        entries = history.conversations(configs.agent, str(Path.cwd().resolve()), day)
        if not entries:
            text_formatter.commander_print(msg.t("No conversation history found."))
            return
        groups = {}
        for entry in entries:
            groups.setdefault((entry["day"], entry["session"]), []).append(entry)
        for (session_day, session_id), turns in groups.items():
            unknown = msg.t("Not recorded")
            display_text(f"### {session_day or unknown} — {msg.t('Session')}: `{session_id or unknown}`")
            for turn in turns:
                display_text(f"**{msg.t('Question')}** ({turn['created']})\n\n{turn['question']}")
                if turn["answer"] is not None:
                    display_text(f"**{msg.t('Answer')}**\n\n{turn['answer']}")
                elif turn["error"] is not None:
                    display_text(f"**{msg.t('Failed')}**\n\n{turn['error']}")
                else:
                    display_text(msg.t("Incomplete request: no final answer recorded."))

    @staticmethod
    def history_forget() -> None:
        """Forget entries pushed to the history."""
        KeyboardInput.forget_history()
