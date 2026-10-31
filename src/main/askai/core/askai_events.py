#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.askai_events
      @file: askai_events.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""

from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.exception.exceptions import InvalidArgumentError
from hspylib.core.namespace import Namespace
from hspylib.modules.eventbus.fluid import FluidEvent, FluidEventBus

ASKAI_BUS_NAME: str = "askai-reply-bus"

TTS_FALLBACK_EVENT: str = "askai-tts-fallback-event"

ABORT_EVENT: str = "askai-abort-event"

REPLY_EVENT: str = "askai-reply-event"

MIC_LISTENING_EVENT: str = "askai-mic-listening-event"

DEVICE_CHANGED_EVENT: str = "askai-input-device-changed-event"

MODE_CHANGED_EVENT: str = "askai-routing-mode-changed-event"


class AskAiEvents(Enumeration):
    """Facility class to provide easy access to AskAI events."""

    # fmt: off
    ASKAI_BUS = FluidEventBus(
        ASKAI_BUS_NAME,
        tts_fallback=FluidEvent(TTS_FALLBACK_EVENT, provider="", reason=""),
        abort=FluidEvent(ABORT_EVENT, message=None),
        reply=FluidEvent(REPLY_EVENT, erase_last=False),
        listening=FluidEvent(MIC_LISTENING_EVENT, listening=True, text=""),
        device_changed=FluidEvent(DEVICE_CHANGED_EVENT, device=None),
        mode_changed=FluidEvent(MODE_CHANGED_EVENT, mode=None, sum_path=None, glob=None),
    )
    # fmt: on

    @staticmethod
    def bus(bus_name: str) -> FluidEventBus:
        """Return an event bus instance for the given name.
        :param bus_name: The name of the event bus to retrieve.
        :return: An instance of FluidEventBus if found; otherwise, None.
        """
        if not (ret_bus := next((b.bus for b in AskAiEvents.values() if b.name == bus_name), None)):
            raise InvalidArgumentError(f"bus '{bus_name}' does not exist!")
        return ret_bus

    def __init__(self, bus: FluidEventBus):
        self._bus = bus

    @property
    def events(self) -> Namespace:
        return self.value.events


events: Namespace = AskAiEvents.ASKAI_BUS.events
