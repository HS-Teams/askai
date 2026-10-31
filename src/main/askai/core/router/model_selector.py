#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.router.model_selector
      @file: model_selector.py
   @created: Tue, 24 Jun 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.core.askai_prompt import prompt
from askai.core.support.inference import complete
from askai.core.component.geo_location import geo_location
from askai.core.engine.openai.temperature import Temperature
from askai.core.enums.response_model import ResponseModel
from askai.core.model.model_result import ModelResult
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.object_mapper import object_mapper


class ModelSelector(metaclass=Singleton):
    """Utility class to query the LLM for selecting the appropriate model to process user requests. This class
    facilitates the selection of the most suitable model based on the nature of the user's query, ensuring optimal
    processing and response generation.
    """

    INSTANCE: "ModelSelector"

    def select_model(self, question: str) -> ModelResult:
        """Select the appropriate response model based on the given human question.
        :param question: The user's query used to determine the most suitable model.
        :return: An instance of ModelResult representing the selected model.
        """
        final_prompt: str = prompt.read_prompt("model-select.txt").format(
            datetime=geo_location.datetime, models=ResponseModel.enlist(), question=question
        )
        if response := complete(final_prompt, Temperature.DATA_ANALYSIS.temp):
            json_string: str = response
            model_result: ModelResult | str = object_mapper.of_json(json_string, ModelResult)
            model_result: ModelResult = model_result if isinstance(model_result, ModelResult) else ModelResult.default()
        else:
            model_result: ModelResult = ModelResult.default()

        return model_result


assert (selector := ModelSelector().INSTANCE) is not None
