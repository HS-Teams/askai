#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.router.tools.browser
      @file: browser.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.geo_location import geo_location
from askai.core.component.internet_service import internet
from askai.core.engine.openai.temperature import Temperature
from askai.core.model.search_result import SearchResult
from askai.core.router.tools.terminal import execute_bash
from askai.core.support.shared_instances import shared
from typing import Optional
from urllib.parse import urlparse

import logging as log
from askai.core.support.inference import complete


def open_url(url: str) -> str:
    """Opens a URL specified by the given path name.
    :param url: The URL to be opened.
    :return: A string telling whether the URL was successfully opened or not.
    """
    # Check if it's a valid URL
    if (parsed_url := urlparse(url)) and parsed_url.scheme and parsed_url.netloc:
        status, _ = execute_bash(f"open {url}")
        if status:
            return f"`{url}` was successfully opened!"
    return f"Unable to open URL: '{url}'"


def browse(query: str, search_engine) -> Optional[str]:
    """Fetch the information from the Internet.
    :param query: The search query.
    """
    # fmt: off
    template = prompt.read_prompt("search-builder")
    final_prompt: str = template.format(
        idiom=shared.idiom, datetime=geo_location.datetime,
        location=geo_location.location, question=query
    )
    # fmt: on
    log.info("Browser::[QUESTION] '%s'  context=''", final_prompt)
    response = complete(final_prompt, Temperature.DATA_ANALYSIS.temp)

    if response and shared.UNCERTAIN_ID not in response:
        search: SearchResult = SearchResult.parse_response(query, response)
        if not isinstance(search, SearchResult):
            log.error(msg.invalid_response(search))
            output = response.strip()
        else:
            output = internet.google_search(search)
            if not output:
                output = msg.search_empty()
    else:
        output = "Sorry, I don't know."

    return output
