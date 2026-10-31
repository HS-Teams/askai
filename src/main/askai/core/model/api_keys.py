#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.askai_configs
      @file: askai_configs.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.exception.exceptions import MissingApiKeyError
from clitt.core.tui.minput.input_validator import InputValidator
from clitt.core.tui.minput.menu_input import MenuInput
from clitt.core.tui.minput.minput import minput
from hspylib.core.enums.charset import Charset
from pathlib import Path
from pydantic.v1 import BaseSettings, Field
from typing import Optional

import dotenv
import os

API_KEY_FILE: str = os.environ.get("HHS_ENV_FILE", str(os.path.join(Path.home(), ".env")))

dotenv.load_dotenv(API_KEY_FILE)


class ApiKeys(BaseSettings):
    """A class to manage and handle the required API keys.
    This class provides a structured way to store, access, and manage API keys necessary for various services.
    It inherits from BaseSettings to facilitate environment-based configuration.
    """

    # fmt: off
    OPENAI_API_KEY: Optional[str] = Field(None, description="Open AI Api Key")
    GOOGLE_API_KEY: Optional[str] = Field(None, description="Google Api Key")
    DEEPL_API_KEY: Optional[str]  = Field(None, description="DeepL Api Key")
    # fmt: on

    def has_key(self, key_name: str) -> bool:
        """Check if the specified API key exists and is not empty.
        :param key_name: The name of the API key to check.
        :return: True if the API key exists and is not empty, otherwise False.
        """
        api_key: str = key_name.upper()
        return hasattr(self, api_key) and ((kv := getattr(self, api_key)) is not None and len(kv) > 0)

    class Config:
        """Configuration class for setting environment variables related to API keys."""

        env_file = API_KEY_FILE
        env_file_encoding = Charset.UTF_8.val

    @staticmethod
    def prompt() -> bool:
        """Prompt the user to input the required API keys.
        :return: True if all required API keys are successfully provided, otherwise False.
        """

        # fmt: off
        form_fields = MenuInput.builder() \
            .field() \
                .label('OPENAI_API_KEY') \
                .value(os.environ.get("OPENAI_API_KEY")) \
                .min_max_length(51, 51) \
                .validator(InputValidator.anything()) \
                .build() \
            .field() \
                .label('GOOGLE_API_KEY') \
                .value(os.environ.get("GOOGLE_API_KEY")) \
                .min_max_length(39, 39) \
                .validator(InputValidator.anything()) \
                .build() \
            .field() \
                .label('DEEPL_API_KEY') \
                .value(os.environ.get("DEEPL_API_KEY")) \
                .min_max_length(39, 39) \
                .validator(InputValidator.anything()) \
                .build() \
            .build()
        # fmt: on

        if result := minput(form_fields, "Please fill the required ApiKeys"):
            with open(API_KEY_FILE, "r+", encoding=Charset.UTF_8.val) as f_envs:
                envs = f_envs.readlines()
            with open(API_KEY_FILE, "w", encoding=Charset.UTF_8.val) as f_envs:
                all_envs: set[str] = set(map(str.strip, envs))
                for key, value in zip(result.attributes, result.values):
                    os.environ[key.upper()] = value
                    all_envs.add(f"export {key.upper()}={value}")
                final_envs: list[str] = list(all_envs)
                final_envs.sort()
                f_envs.write(os.linesep.join(final_envs))
            return True

        return False

    def ensure(self, api_key: str, feature: str) -> None:
        """Ensure that the provided API key is valid for the required method.
        :param api_key: The API key to check.
        :param feature: The feature for which the API key is required.
        :raises MissingApiKeyError: If the API key is not valid.
        """
        if not self.has_key(api_key):
            raise MissingApiKeyError(f"ApiKey '{api_key}' is required to use '{feature}'")
