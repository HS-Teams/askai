"""Text conversions for stored history and tool results."""
import os
import re
from typing import AnyStr
from hspylib.core.tools.text_tools import ensure_endswith, ensure_startswith, strip_escapes


def ensure_ln(text: str, separator: str = os.linesep) -> str:
    """Ensure the text starts and ends with a line separator.
    :param text: The text to be formatted.
    :param separator: The line separator to use (default is the system's line separator).
    :return: The formatted text with the specified line separator at the beginning and end.
    """
    return ensure_endswith(ensure_startswith(text, separator), separator * 2)


def _remove_markdown(text: AnyStr) -> str:
    """Remove Markdown formatting from a string.
    :param text: The input string potentially containing Markdown formatting.
    :return: The input string with Markdown formatting removed.
    """
    plain_text = re.sub(r"```(.*?)```", r"\1", str(text), flags=re.DOTALL)
    plain_text = re.sub(r"`[^`]+`", "", plain_text)
    plain_text = re.sub(r"^(#+\s+)", "", plain_text)
    plain_text = re.sub(r"\*\*([^*]+)\*\*", r"\1", plain_text)
    plain_text = re.sub(r"\*([^*]+)\*", r"\1", plain_text)
    plain_text = re.sub(r"__([^_]+)__", r"\1", plain_text)
    plain_text = re.sub(r"_([^_]+)_", r"\1", plain_text)
    plain_text = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", plain_text)
    plain_text = re.sub(r"!\[([^]]*)]\([^)]+\)", r"\1", plain_text)
    plain_text = re.sub(r"---|___|\*\*\*", "", plain_text)
    plain_text = re.sub(r">\s+", "", plain_text)
    plain_text = re.sub(r"[-*+]\s+", "", plain_text)
    plain_text = re.sub(r"^\d+\.\s+", "", plain_text)

    return plain_text


def strip_format(text: AnyStr) -> str:
    """Remove the markdown formatting and ANSI escape codes from the text.
    :param text: The input string containing markdown formatting and ANSI escape codes.
    :return: A string with the formatting removed.
    """
    return strip_escapes(_remove_markdown(str(text)))
