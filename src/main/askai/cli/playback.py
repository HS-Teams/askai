"""Interactive controls for AskAI-owned media, outside the assistant conversation."""
from pathlib import Path
from time import sleep
from hspylib.modules.cli.keyboard import Keyboard
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from askai.core.capabilities.desktop import DesktopCapabilities
from askai.core.capabilities.media_player import PlaybackEnded

FEEDBACK_SECONDS = 0.4
CONTROLS = [('p', 'Resume playback'), ('a', 'Pause playback'), ('s', 'Stop playback'),
            ('+', 'Volume up'), ('-', 'Volume down'), ('q', 'Close')]


def read_playback_key():
    key = Keyboard.wait_keystroke(ignore_error_keys=True)
    return key.value if key is not None else ''


def show_player(player, console, read, translate):
    status = player.status()
    if status is None:
        console.print(translate('No active AskAI media playback'))
        return
    path = Path(status['path'])
    kind = 'Video' if path.suffix.lower() in DesktopCapabilities.VIDEO_SUFFIXES else 'Audio'
    body = Text(path.name + '\n', style='bold')
    body.append(translate(kind) + '\n', style='cyan')
    console.print(Panel(body, title='Playback', border_style='cyan'))
    controls = '  '.join(f'[{key}] {translate(label)}' for key, label in CONTROLS)

    def line():
        return Text(translate({'playing': 'Media playing', 'paused': 'Media paused'}[status['state']]) + ' · ' + translate('System volume') +
                    f": {player.volume()}% · " + controls, style='cyan', no_wrap=True, overflow='ellipsis')

    with Live(line(), console=console, auto_refresh=False) as live:
        while True:
            action = (read() or '').lower()
            if action in ('q', '\x1b', '\r', '\n'):
                return
            label = dict(CONTROLS).get(action)
            if action in ('+', '-'):
                player.volume(5 if action == '+' else -5)
            elif action in ('p', 'a', 's'):
                try:
                    player.control({'p': 'play', 'a': 'pause', 's': 'stop'}[action])
                except PlaybackEnded:
                    live.update(Text(translate('Playback has ended')), refresh=True)
                    return
            else:
                label = 'Unknown playback control'
            live.update(Text(translate(label), style='bold yellow'), refresh=True)
            sleep(FEEDBACK_SECONDS)
            status = player.status()
            if status is None:
                live.update(Text(translate('No active AskAI media playback')), refresh=True)
                return
            live.update(line(), refresh=True)
