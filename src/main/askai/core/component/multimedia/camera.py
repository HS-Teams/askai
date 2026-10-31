#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@project: HsPyLib-AskAI
@package: askai.core.components
   @file: recorder.py
@created: Wed, 22 Feb 2024
 @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
   @site: https://github.com/yorevs/askai
@license: MIT - Please refer to <https://opensource.org/licenses/MIT>

Copyright (c) 2024, AskAI
"""

from __future__ import annotations

from time import monotonic
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.component.cache_service import PHOTO_DIR
from askai.core.component.multimedia.audio_player import player
from askai.core.model.ai_reply import AIReply
from askai.core.support.utilities import build_img_path
from askai.exception.exceptions import CameraAccessFailure, WebCamInitializationFailure
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.zoned_datetime import now_ms
from retry import retry

import atexit
import cv2
import logging as log
import pause


class Camera(metaclass=Singleton):
    """Provide an interface to interact with the webcam. This class offers methods for controlling and accessing the
    webcam's functionality, ensuring that only one instance interacts with the hardware at a time.
    """

    INSTANCE: "Camera"

    def countdown(self, count: int) -> None:
        """Show each count while reading fresh frames for automatic exposure."""
        for remaining in range(count, 0, -1):
            events.reply.emit(reply=AIReply.mute(msg.smile(remaining)), erase_last=remaining != count)
            player.play_sfx("click")
            deadline = monotonic() + 1
            while monotonic() < deadline:
                ok, frame = self._cam.read()
                if not ok or frame is None:
                    raise CameraAccessFailure("Failed to read camera during countdown")
                pause.milliseconds(10)

    def capture_frame(self, filename: str | None = None, countdown: int = 3) -> str:
        """Capture locally without initializing image stores or calling a vision API."""
        try:
            self.initialize()
            self.countdown(countdown)
            ok, frame = self._cam.read()
            if not ok or frame is None:
                raise CameraAccessFailure("Failed to take a photo from WebCam!")
            target = build_img_path(PHOTO_DIR, filename or str(now_ms()), "-PHOTO.jpg")
            if not target or not cv2.imwrite(target, frame):
                raise CameraAccessFailure("Could not save camera image")
            events.reply.emit(reply=AIReply.mute(msg.click()), erase_last=True)
            player.play_sfx("camera-shutter")
            return target
        finally:
            self.shutdown()

    def __init__(self):
        self._cam = None

    @retry(tries=3, backoff=1, delay=1)
    def initialize(self) -> None:
        """Initialize the camera device."""
        if not self._cam or not self._cam.isOpened():
            self._cam = cv2.VideoCapture(0)
            ret, img = self._cam.read()
            log.info("Starting the WebCam device")
            if not (ret and img is not None):
                raise WebCamInitializationFailure("Failed to initialize the WebCam device !")
            else:
                atexit.register(self.shutdown)

    @retry(tries=3, backoff=1, delay=1)
    def shutdown(self) -> None:
        """Shutdown the camera device."""
        if self._cam and self._cam.isOpened():
            log.info("Shutting down the WebCam device")
            self._cam.release()


assert (camera := Camera().INSTANCE) is not None
