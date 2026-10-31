"""Localize display prose without changing protocol identifiers or commands."""

from copy import deepcopy


def translate_request(params: dict, translate) -> dict:
    localized = deepcopy(params)
    for key in ("message", "reason"):
        if params.get(key):
            localized[key] = translate(params[key])
    for question in localized.get("questions", []):
        question["question"] = translate(question["question"])
        for option in question.get("options") or []:
            if option.get("label"):
                option["label"] = translate(option["label"])
            if option.get("description"):
                option["description"] = translate(option["description"])
    return localized
