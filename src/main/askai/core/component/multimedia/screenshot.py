"""Original AskAI screenshot capture, independent of vision providers."""
from pathlib import Path
from threading import Event
from hspylib.core.zoned_datetime import now_ms


def capture_screenshot(cancelled: Event) -> str | None:
    import pyautogui
    import pause
    from askai.core.askai_events import events
    from askai.core.askai_messages import msg
    from askai.core.component.cache_service import SCREENSHOTS_DIR
    from askai.core.component.multimedia.audio_player import player
    from askai.core.model.ai_reply import AIReply

    for remaining in (3, 2, 1):
        if cancelled.is_set():
            return None
        events.reply.emit(reply=AIReply.mute(msg.t(f"Screenshot in: {remaining}")), erase_last=remaining != 3)
        player.play_sfx('ui/click')
        pause.seconds(1)
    if cancelled.is_set():
        return None
    target = Path(SCREENSHOTS_DIR) / f'ASKAI-SCREENSHOT-{now_ms()}.jpeg'
    screenshot = pyautogui.screenshot()
    try:
        rgb = screenshot.convert('RGB')
        try:
            rgb.save(str(target))
        finally:
            rgb.close()
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    finally:
        screenshot.close()
    player.play_sfx('ui/camera-shutter')
    events.reply.emit(reply=AIReply.mute(msg.click()), erase_last=True)
    events.reply.emit(reply=AIReply.debug(msg.screenshot_saved(str(target))))
    return str(target)
