#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.support.utilities
      @file: utilities.py
   @created: Wed, 10 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from types import SimpleNamespace
from typing import AnyStr, Optional, TypeVar

import json
import os
import re

T = TypeVar("T")


def ensure_parseable(content: str) -> Optional[str]:
    """Ensures the given content is a parseable JSON array by adjusting it if necessary.
    :param content: A string containing the content to be parsed.
    :return: A JSON array string if the content is parseable; otherwise, None.
    """
    if not content:
        return None
    if content.startswith("["):
        # Content is already a JSON array
        return content
    # Process lines to extract JSON objects
    lines = content.split(os.linesep)
    json_objects: list[str] = list()
    for line in lines:
        if not (line := line.strip()):
            continue  # Skip empty lines
        if line.startswith("-"):
            line = line.lstrip("-").strip()
        json_objects.append(line)
    # Wrap in square brackets to form a JSON array
    return f"[{','.join(json_objects)}]"


def parse_field(field_name: AnyStr, text: AnyStr) -> Optional[T]:
    """Parse the LLM response and extract a specified field.
    :param field_name: The name of the field to be extracted.
    :param text: The text from which to extract the field.
    :return: The extracted field value, or None if not found.
    """
    flags: int = re.IGNORECASE | re.MULTILINE | re.DOTALL
    field_pattern: str = field_name + r':\s*\"?(.+?)(["@])*$'
    field_matcher: re.Match[str] | None = re.search(field_pattern, text, flags)
    field_value: str = field_matcher.group(1) if field_matcher else None
    return field_value.strip() if field_value else None


def parse_word(word: AnyStr, text: AnyStr) -> Optional[T]:
    """Parse the LLM response and extract a specified word attribute.
    :param word: The word attribute to extract from the text.
    :param text: The text from which to extract the word attribute.
    :return: The extracted word attribute if found; otherwise, None.
    """
    flags: int = re.IGNORECASE | re.MULTILINE | re.DOTALL
    word_pattern: str = r"[*_\s]*" + word + r':[*_\s]*(.+)["@]'
    word_matcher: re.Match[str] | None = re.search(word_pattern, text, flags)
    word_value: str = word_matcher.group(1) if word_matcher else None
    return word_value.strip() if word_value else None


def parse_list(field_name: AnyStr, text: AnyStr, is_dict: bool = True) -> list[SimpleNamespace | AnyStr]:
    """Parse the LLM response and extract a specified list.
    :param field_name: The name of the field to extract from the text.
    :param text: The text response from the LLM to parse.
    :param is_dict: Whether list list contains dicts or strings.
    :return: A list of SimpleNamespace objects or strings.
    """
    flags: int = re.IGNORECASE | re.DOTALL
    list_pattern: str = re.escape(field_name) + r":[ \t]*(.*?)(?:\r?\n[ \t]*@|$)"
    list_matcher: re.Match[str] | None = re.search(list_pattern, text, flags)
    if list_matcher:
        extracted_list: str = list_matcher.group(1).strip()
        list_value: list[str | dict] = json.loads(ensure_parseable(extracted_list))
        if not isinstance(list_value, list):
            raise ValueError(f"Expected a list for {field_name}")
        if is_dict:
            if not all(isinstance(val, dict) for val in list_value):
                raise ValueError(f"Expected objects in {field_name}")
            return [SimpleNamespace(**value) for value in list_value]
        return list_value
    return list()
