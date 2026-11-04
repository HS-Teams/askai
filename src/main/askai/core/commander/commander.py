#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@project: HsPyLib-AskAI
@package: askai.core.commander.commander
   @file: commander.py
@created: Thu, 25 Apr 2024
 @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
   @site: https://github.com/yorevs/askai
@license: MIT - Please refer to <https://opensource.org/licenses/MIT>

Copyright (c) 2024, AskAI
"""
from os.path import basename
from pathlib import Path
from string import Template
from textwrap import dedent
import os

from askai.cli.help_formatter import HelpGroup, render_help
from askai.cli.gestures_help import GesturesCommand
from click import Command
from clitt.core.term.cursor import cursor
from hspylib.core.config.path_object import PathObject
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import sysout, to_bool
from hspylib.modules.eventbus.event import Event
import click

from askai.core.askai_configs import configs
from askai.core.askai_events import ASKAI_BUS_NAME, AskAiEvents, events, REPLY_EVENT
from askai.core.commander.commands.cache_cmd import CacheCmd
from askai.core.commander.commands.camera_cmd import CameraCmd
from askai.core.commander.commands.general_cmd import GeneralCmd
from askai.core.commander.commands.history_cmd import HistoryCmd
from askai.core.commander.commands.settings_cmd import SettingsCmd
from askai.core.commander.commands.tts_stt_cmd import TtsSttCmd
from askai.core.component.rag_provider import RAG_EXT_DIR, RAGProvider
from askai.core.enums.router_mode import RouterMode
from askai.core.support.shared_instances import shared
from askai.cli import output as cli_output
from askai.language.language import AnyLocale, Language

# fmt: off
COMMANDER_HELP_TPL = Template(
    dedent("""\
    # AskAI Commander - HELP

    > Commands:

    ${commands}
    ---

    > CLI-Input Key-Bindings:

    | **Key**  | **Action**                    |
    | -------- | ----------------------------- |
    | *Ctrl+L* | **Activate Push-To-Talk.**    |
    | *Ctrl+R* | **Reset the input field.**    |
    | *Ctrl+F* | **Forget the input history.** |
    | *Ctrl+D* | **Exit the application.**     |

    >   Use '/<command> --help' or '/help \\<command\\>'
    """))

# fmt: on

RE_ASKAI_CMD: str = r"^(?<!\\)/(\w+)( (.*))*$"

def commands() -> list[str]:
    """Return slash commands from the same registry used for execution."""
    return sorted((f"/{name}" for name in ask_commander.commands), reverse=True)


def command_suggestions() -> list[str]:
    """Expose commands, standard help and declared operation choices to LineInput."""
    suggestions = set(commands())
    for name, command in ask_commander.commands.items():
        suggestions.add(f"/{name} --help")
        arguments = [param for param in command.params if isinstance(param, click.Argument)]
        if arguments and isinstance(arguments[0].type, click.Choice):
            suggestions.update(f"/{name} {choice}" for choice in arguments[0].type.choices)
    return sorted(suggestions, key=lambda value: (" " in value, value))


def commander_help(command: str | None = None) -> str:
    """Use Click's registered descriptions and usage for command help."""
    if command:
        if cmd := ask_commander.commands.get(command):
            return _format_help(cmd)
        raise click.UsageError(f"No such command: /{command}")
    rows = "| Command | Description |\n| --- | --- |\n"
    for name, cmd in sorted(ask_commander.commands.items()):
        description = (cmd.help or "").splitlines()[0]
        rows += f"| `/{name}` | {description} |\n"
    return COMMANDER_HELP_TPL.substitute(commands=rows)


def is_command(string: str) -> bool:
    """Check whether a slash command is registered."""
    return string in commands()


def _format_help(command: Command) -> str:
    """Keep argument requirements, choices and options in sync with Click."""
    with click.Context(command, info_name=f"/{command.name}") as context:
        return command.get_help(context)


def _format_toggle(condition: bool, true_text: str = "ON", false_text: str = "OFF") -> str:
    """Render a toggle using the shared Markdown theme and a state icon."""
    return " **" + true_text + "**" if condition else " **" + false_text + "**"


def _init_context(context_size: int = 1000, engine_name: str = "openai", model_name: str = "gpt-4o-mini") -> None:
    """Initialize the AskAI context and startup components.
    :param context_size: The maximum size of the context window (default is 1000).
    :param engine_name: The name of the engine to initialize (default is "openai").
    :param model_name: The model name of the engine to initialize (default is "gpt-3.5-turbo").
    """

    def _reply_event(ev: Event, error: bool = False) -> None:
        """Callback for handling the reply event.
        :param ev: The event object representing the reply event.
        :param error: Indicates whether the reply contains an error (default is False).
        """
        if message := ev.args.message:
            if error:
                cli_output.render_command(f"{message}!")
            else:
                if ev.args.erase_last:
                    cursor.erase_line()
                cli_output.render_message(message)

    if shared.engine is None and shared.context is None:
        shared.create_engine(engine_name=engine_name, model_name=model_name, mode=RouterMode.default())
        shared.create_context(context_size)
        askai_bus = AskAiEvents.bus(ASKAI_BUS_NAME)
        askai_bus.subscribe(REPLY_EVENT, _reply_event)


@click.group(cls=HelpGroup)
@click.pass_context
def ask_commander(_) -> None:
    """AskAI commands group. This function serves as the entry point for the AskAI command-line interface (CLI)
    commands, grouping related commands together.
    """
    _init_context()


@ask_commander.command()
@click.argument("command", default="")
def help(command: str) -> None:
    """Display the help message for the specified command and exit. If no command is provided, it displays the general
    help message.
    :param command: The command to retrieve help for (optional).
    """
    render_help(cli_output.console, commander_help(command.replace("/", "")), overview=not command)


@ask_commander.command()
@click.argument('operation', type=click.Choice(['list', 'set']), default='list')
@click.argument('name', required=False)
def engine(operation: str, name: str | None) -> dict:
    """List engines or switch the active engine between turns, preserving context."""
    return _runtime_selection('engine', operation, name)


@ask_commander.command()
@click.argument('operation', type=click.Choice(['list', 'set']), default='list')
@click.argument('name', required=False)
def model(operation: str, name: str | None) -> dict:
    """List models for the active engine or select one, preserving context."""
    return _runtime_selection('model', operation, name)


def _runtime_selection(kind, operation, name):
    from askai.core.engine.runtime import runtime_engines

    if operation == 'set' and not name:
        raise click.UsageError(f'Usage: /{kind} set <name>')
    if operation == 'list' and name:
        raise click.UsageError(f'Usage: /{kind} list')
    try:
        runtime = runtime_engines()
        if operation == 'set':
            result = runtime.set_engine(name) if kind == 'engine' else runtime.set_model(name)
        else:
            result = runtime.engines() if kind == 'engine' else runtime.models()
        cli_output.render_command(f"Engine: `{result['engine']}` · Model: `{result['model']}`")
        for item in result.get('engines', []):
            cli_output.render_command(item)
        for item in result.get('models', []):
            cli_output.render_command(f"`{item['id']}` — {item['name']}")
        return result
    except Exception as error:
        raise click.ClickException(str(error)) from error


@ask_commander.command()
@click.argument("operation", type=click.Choice(["reset", "compact"]))
def session(operation: str) -> None:
    """Reset or compact the current agent session, preserving history and STM.

    /session compact summarizes native context while keeping the session ID.
    /session reset starts a new session on the next request.
    """
    from askai.core.processors.taius import taius
    from askai.core.askai_messages import msg

    if operation == "compact":
        changed = taius.compact_session()
        cli_output.render_command(msg.t(
            "Session compacted. History and STM were preserved." if changed
            else "No new session activity to compact."
        ))
        return
    taius.reset_session()
    cli_output.render_command(msg.t(
        "Session reset. Your next request will start a new session with the AskAI tool prompt. History and STM were preserved."
    ))


@ask_commander.command()
def assistive() -> None:
    """Toggle assistive mode ON/OFF."""
    SettingsCmd.set("askai.router.assistive.enabled", not configs.is_assistive, announce=False)
    cli_output.render_command(f"`Assistive responses` is {_format_toggle(configs.is_assistive)}")


@ask_commander.command()
def debug() -> None:
    """Toggle debug mode ON/OFF."""
    SettingsCmd.set("askai.debug.enabled", not configs.is_debug, announce=False)
    cli_output.render_command(f"`Debugging` is {_format_toggle(configs.is_debug)}")


@ask_commander.command()
def speak() -> None:
    """Toggle speak mode ON/OFF."""
    SettingsCmd.set("askai.speak.enabled", not configs.is_speak, announce=False)
    cli_output.render_command(f"`Speech-To-Text` is {_format_toggle(configs.is_speak)}")


@ask_commander.command()
def mute() -> None:
    """Toggle sound-effect muting and remember the preference. Speech uses /speak."""
    SettingsCmd.set("askai.sfx.muted", not configs.is_sfx_muted, announce=False)
    cli_output.render_command(f"`SFX mute` is {_format_toggle(configs.is_sfx_muted)}")


@ask_commander.command()
@click.argument("operation", default="list")
@click.argument("name", default="ALL")
def context(operation: str, name: str | None = None) -> None:
    """Manage the current chat context window.
    :param operation: The operation to perform on contexts. Options: [list | forget].
    :param name: The name of the context to target (default is "ALL").
    """
    match operation.casefold():
        case "list":
            HistoryCmd.context_list()
        case "forget":
            HistoryCmd.context_forget(name)
        case _:
            err = str(click.BadParameter(f"Invalid settings operation: '{operation}'"))
            cli_output.render_command(f"Error: {err}")


@ask_commander.command()
@click.argument("operation", type=click.Choice(["list", "enable", "forget"]), default="list")
@click.argument("value", required=False)
def history(operation: str, value: str | None = None) -> None:
    """List session conversations, configure resume, or forget keyboard input.

    /history list [YYYY-MM-DD] lists all dates when omitted.
    /history enable <0|1> controls saving conversations and resuming sessions.
    /history forget clears keyboard input only; /session reset starts a new session.
    """
    match operation:
        case "list":
            if value:
                from datetime import date
                try:
                    date.fromisoformat(value)
                except ValueError as error:
                    raise click.BadParameter("Use a date in YYYY-MM-DD format.") from error
            HistoryCmd.history_list(value)
        case "enable":
            if value not in ("0", "1"):
                raise click.BadParameter("Usage: /history enable <0|1>")
            SettingsCmd.set("askai.context.keep.conversation", value == "1")
        case "forget":
            if value is not None:
                raise click.BadParameter("Usage: /history forget")
            HistoryCmd.history_forget()


@ask_commander.command()
@click.argument("name", default="LAST_REPLY")
def copy(name: str) -> None:
    """Copy the specified context entry to the clipboard.
    :param name: The name of the context entry to copy.
    """
    HistoryCmd.context_copy(name)


@ask_commander.command()
@click.option('--delay', type=click.FloatRange(min=0), default=3.0, show_default=True,
              help='Seconds to switch focus before pasting.')
def paste(delay: float) -> None:
    """Paste at the caret in the focused macOS app using Cmd+V, without pressing Enter.

    Switch to the destination app during the delay. The app focused when the delay
    ends receives the paste. Use --delay 0 to paste immediately.
    """
    from time import sleep
    import pyperclip
    from askai.core.support.clipboard import paste_into_focused_app

    try:
        if not pyperclip.paste():
            cli_output.render_command('The clipboard is empty.')
            return
        cli_output.render_command(f'Pasting in {delay:g} seconds. Focus the destination app.')
        cli_output.console.file.flush()
        sleep(delay)
        paste_into_focused_app()
    except (OSError, RuntimeError) as error:
        raise click.ClickException(str(error)) from error


@ask_commander.command()
@click.argument("operation", default="list")
@click.argument("name", default="")
def devices(operation: str, name: str | None = None) -> None:
    """Manages the audio input devices.
    :param operation: Specifies the device operation. Options: [list|set].
    :param name: The target device name for setting.
    """
    match operation.casefold():
        case "list":
            TtsSttCmd.device_list()
        case "set":
            TtsSttCmd.device_set(name)
        case _:
            err = str(click.BadParameter(f"Invalid settings operation: '{operation}'"))
            cli_output.render_command(f"Error: {err}")


@ask_commander.command()
@click.argument("operation", default="list")
@click.argument("name", default="")
@click.argument("value", default="")
def settings(operation: str, name: str, value: str) -> None:
    """Handles modifications to AskAI settings.
    :param operation: The action to perform on settings. Options: [list|get|set|reset]
    :param name: The key for the setting to modify.
    :param value: The new value for the specified setting.
    """
    match operation.casefold():
        case "list":
            SettingsCmd.list(name)
        case "get":
            SettingsCmd.get(name)
        case "set":
            SettingsCmd.set(name, value)
        case "reset":
            SettingsCmd.reset()
        case _:
            err = str(click.BadParameter(f"Invalid settings operation: '{operation}'"))
            cli_output.render_command(f"Error: {err}")


@ask_commander.command()
@click.argument("operation", type=click.Choice(["list", "get", "set", "reset"]), default="list")
@click.argument("name", default="")
@click.argument("value", type=click.Choice(["ask", "allow", "deny", "never", ""]), default="")
def grants(operation: str, name: str, value: str) -> None:
    """Manage persistent permissions using AskAI settings.

    /grants list [prefix]
    /grants get camera.capture.local
    /grants set media.play.local allow
    /grants reset [name]: restore ask for one or all grants.
    Full askai.grants.* names are also accepted. No wildcard grants.
    """
    from askai.core.commander.commands.grants_cmd import GrantsCmd
    try:
        GrantsCmd.run(operation, name, value)
    except ValueError as error:
        raise click.BadParameter(str(error)) from error


@ask_commander.command()
@click.argument("operation", default="list")
@click.argument("args", nargs=-1)
def cache(operation: str, args: tuple[str, ...]) -> None:
    """Manage response, audio and translation caches. /cache enable <0|1> controls all three.
    TTL applies to the response cache only.
    :param operation: Specifies the cache operation. Options: [list|get|clear|files|enable|ttl]
    :param args: Arguments relevant to the chosen operation.
    """
    match operation.casefold():
        case "list":
            CacheCmd.list()
        case "get":
            if not args:
                err: str = str(click.MissingParameter(f"Argument 'name' is required. Usage /cache get \\<name\\>"))
                cli_output.render_command(f"Error: {err}")
            else:
                set(map(sysout, map(CacheCmd.get, args)))
        case "clear":
            if args and (invalid := next((a for a in args if not isinstance(a, str | int)), None)):
                err: str = str(click.BadParameter(f"Invalid argument: '{invalid}'"))
                cli_output.render_command(f"Error: {err}")
            elif args:
                set(map(CacheCmd.clear, args))
            else:
                CacheCmd.clear()
        case "files":
            CacheCmd.files("cleanup" in args, *args)
        case "enable":
            if not args:
                err: str = str(click.MissingParameter(f"Arguments missing. Usage /cache enable \\<0|1\\>"))
                cli_output.render_command(f"Error: {err}")
            else:
                SettingsCmd.set("askai.cache.enabled", to_bool(args[0]), announce=False)
                cli_output.render_command(f"Caching has been *{'en' if configs.is_cache else 'dis'}abled* !")
        case "ttl":
            if not args:
                cli_output.render_command(f"Cache TTL is set to *{configs.ttl} minutes* !")
            elif not args[0].isdigit():
                err: str = str(click.MissingParameter(f"Argument 'minutes' is invalid. Usage /cache ttl \\<minutes\\>"))
                cli_output.render_command(f"Error: {err}")
            else:
                configs.ttl = int(args[0])
                cli_output.render_command(f"Cache TTL was set to *{args[0]} minutes* !")
        case _:
            cli_output.render_command(f"`Caching` is {_format_toggle(configs.is_cache)}")


@ask_commander.command()
@click.argument("speed", type=click.INT, default=1)
def tempo(speed: int | None = None) -> None:
    """Manages the speech-to-text tempo.
    :param speed: Desired speech tempo setting. Options: [list|get]
    """
    TtsSttCmd.tempo(speed)


@ask_commander.command()
def usage() -> None:
    """Show remaining Codex, TTS and translator quotas; local free engines show '-'."""
    from askai.core.commander.commands.usage_cmd import UsageCmd

    UsageCmd.show()


@ask_commander.command()
def playback() -> None:
    """Show current audio/video and control play, pause, stop and macOS output volume.

    Closing the mini player leaves playback running. Volume changes affect system output.
    """
    import subprocess
    from askai.cli.playback import show_player, read_playback_key
    from askai.core.capabilities.media_player import MediaPlayer
    from askai.core.support.app_paths import askai_data_dir
    from askai.core.askai_messages import msg

    storage = Path(os.getenv('ASKAI_CAPABILITY_DIR', str(askai_data_dir() / 'cache' / 'capabilities')))
    try:
        show_player(MediaPlayer(storage), cli_output.console, read_playback_key, msg.t)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        raise click.ClickException(str(error)) from error


@ask_commander.command(cls=GesturesCommand)
@click.argument('operation', type=click.Choice(['start', 'stop']), default='start')
@click.option('--camera-index', type=click.IntRange(min=0), default=0, show_default=True)
def gestures(operation: str, camera_index: int) -> dict:
    """Preview hand gestures, move the mouse and pinch to click. Esc stops; no video is recorded."""
    from askai.gestures.command import start
    try:
        if operation == 'stop':
            from askai.gestures.background import stop
            stop()
            return {'status': 'stopped'}
        return start(camera_index)
    except Exception as error:
        raise click.ClickException(str(error)) from error


@ask_commander.command()
@click.argument("operation", default="list")
@click.argument("name", nargs=-1)
def voices(operation: str, name: tuple[str, ...]) -> dict:
    """Manages the active engine speech provider.
    :param operation: The action to perform on voices. Options: [list/set/play]
    :param name: The voice name.
    """
    voice_name = " ".join(name) or None
    try:
        match operation.casefold():
            case "list":
                return TtsSttCmd.voice_list()
            case "set":
                return TtsSttCmd.voice_set(voice_name)
            case "play":
                return TtsSttCmd.voice_play(voice_name)
            case _:
                err = str(click.BadParameter(f"Invalid voices operation: '{operation}'"))
                cli_output.render_command(f"{err}")
                return {'status': 'failed', 'error': err}
    except (RuntimeError, ValueError) as error:
        raise click.ClickException(str(error)) from error


@ask_commander.command()
@click.argument("texts", type=click.STRING, nargs=-1)
@click.option("--dest-dir", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--playback/--no-playback", default=True)
def tts(texts: tuple[str, ...], dest_dir: str, playback: bool) -> None:
    """Convert text to speech using the default AI engine.
    :param texts: The strings to convert. If text represents a valid file, its contents will be used instead.
    :param dest_dir: The directory where the converted audio file will be saved.
    :param playback: Whether to play the audio file after conversion.
    """
    if text := ' '.join(texts):
        f_path: PathObject | None = PathObject.of(text)
        if f_path and f_path.exists and f_path.is_file:
            text = Path(str(f_path)).read_text(encoding=Charset.UTF_8.val)
        TtsSttCmd.tts(text.strip(), dest_dir, playback)


@ask_commander.command()
@click.option("--dest-file", type=click.Path(exists=False, file_okay=True, dir_okay=False))
def dictate(dest_file: str) -> None:
    """Dictate continuously, preserve the original and save a refined copy.

    Press Esc or pause for more than 3 seconds to finish and save. Existing files are never overwritten. Without --dest-file,
    both versions are saved in the AskAI data directory under dictations/.
    The refined text is also copied to the clipboard.
    """
    from sqlite3 import Error as DatabaseError
    from askai.exception.exceptions import InvalidInputDevice, InvalidRecognitionApiError

    try:
        TtsSttCmd.dictate(dest_file)
    except (OSError, ValueError, RuntimeError, DatabaseError,
            InvalidInputDevice, InvalidRecognitionApiError) as error:
        raise click.ClickException(str(error)) from error


@ask_commander.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument("glob", type=click.STRING, default="**/*")
def summarize(folder: str, glob: str) -> None:
    """Create a summary of the folder's contents.
    :param folder: The root directory for the summary.
    :param glob: The file pattern or path to summarize.
    """
    GeneralCmd.summarize(folder, glob)


@ask_commander.command()
@click.option("--locale-str", type=click.STRING, help="The locale identifier, e.g., 'en_US'")
def idiom(locale_str: str) -> None:
    """Set the application's language preference.
    :param locale_str: The locale identifier, e.g., 'en_US'.
    """
    GeneralCmd.idiom(locale_str)


@ask_commander.command()
def info() -> None:
    """Display key information about the running application."""
    if os.getenv("ASKAI_APP"):
        GeneralCmd.app_info()
    else:
        cli_output.render_command("No information available (offline)!")


@ask_commander.command()
@click.argument("from_locale_str")
@click.argument("texts", nargs=-1)
def translate(from_locale_str: AnyLocale, texts: tuple[str, ...]) -> None:
    """Translate text from the source language to the target language.
    :param from_locale_str: The source locale identifier, e.g., 'en_US'.
    :param texts: The list of texts to translate.
    """
    GeneralCmd.translate(Language.of_locale(from_locale_str), " ".join(texts))


@ask_commander.command()
@click.argument("operation", default="capture", type=click.Choice(["capture", "photo", "identify", "id", "register", "review"], case_sensitive=False))
@click.argument("args", nargs=-1)
def camera(operation: str, args: list) -> None:
    """Take photos, identify or register local identities.

    /camera register: capture a photo and ask for names in a numbered preview.
    /camera register "/absolute/photo.jpg" [...]: enroll faces from existing photos.
    /camera review: group stored faces with Merge, Skip or Replace.
    New creates an identity; Merge adds samples; Replace replaces its samples.
    Blank action skips a face; cancelling discards all pending changes.

    :param operation: The camera operation to perform. Options: [capture|identify|register|review]
    :param args: The arguments required for the operation.
    """
    match operation.casefold():
        case "capture" | "photo":
            CameraCmd.capture(*args)
        case "identify" | "id":
            CameraCmd.identify(*args)
        case "register":
            CameraCmd.register(*args)
        case "review":
            CameraCmd.review()
        case _:
            err = str(click.BadParameter(f"Invalid camera operation: '{operation}'"))
            cli_output.render_command(f"{err}")


@ask_commander.command()
@click.argument("router_mode", default="")
def mode(router_mode: str) -> None:
    """Change the AskAI routing mode.
    :param router_mode: The routing mode. Options: [rag|chat|taius]
    """
    if not router_mode:
        cli_output.render_command(f"Available routing modes: **[rag|chat|taius]**. Current: `{shared.mode}`")
    else:
        match router_mode.casefold():
            case "rag":
                events.mode_changed.emit(mode="RAG")
            case "chat":
                events.mode_changed.emit(mode="CHAT")
            case "taius":
                events.mode_changed.emit(mode="TAIUS")
            case _:
                events.mode_changed.emit(mode="DEFAULT")


@ask_commander.command()
@click.argument("operation", default="list")
@click.argument("args", nargs=-1)
def rag(operation: str, args: tuple[str, ...]) -> None:
    """Manages AskAI RAG features.
    :param operation: Specifies the rag operation. Options: [list|add|del|clear|enable]
    :param args: Arguments relevant to the chosen operation.
    """
    match operation.casefold():
        case "add":
            if not args:
                err: str = str(click.MissingParameter(f"Arguments missing. Usage /rag add \\<folder|file\\>"))
                cli_output.render_command(f"Error: {err}")
            else:
                res: Path = Path(args[0])
                if not res.exists():
                    cli_output.render_command(f"Error: Could not find folder: '{res}'")
                else:
                    if RAGProvider.copy_rag(res):
                        cli_output.render_command(f"RAG folder '{res}' has been *added* to rag directory !")
                    else:
                        cli_output.render_command(f"Error: Failed to add RAG folder: '{res}' !")
        case "list":
            sysout(f"> Listing ARG entries from: `{RAG_EXT_DIR}`", markdown=True)
            results = list()
            for entry in sorted(RAG_EXT_DIR.iterdir()):
                pathname: str = basename(entry)
                if pathname.startswith(".") or pathname == "rag-documents.txt":
                    continue
                entry_str: str = "  " if entry.is_dir() else "  "
                results.append(f"- **{entry_str}:** {pathname + ('/' if entry.is_dir() else '')}")
            sysout(os.linesep.join(sorted(results)), markdown=True)
        case "del":
            if not args:
                err: str = str(click.MissingParameter(f"Arguments missing. Usage /rag del \\<folder|file\\>"))
                cli_output.render_command(f"Error: {err}")
            else:
                res: Path = Path(args[0])
                if RAGProvider.del_rag(res):
                    cli_output.render_command(f"RAG resource '{res}' has been *deleted* from rag directory !")
                else:
                    cli_output.render_command(f"Error: Failed to delete RAG folder: '{res}' !")
        case "clear":
            if RAGProvider.clear():
                cli_output.render_command(f"ALL RAG resources been *deleted* from rag directory !")
            else:
                cli_output.render_command(f"Error: Failed to wipe the RAG folder!")
        case "enable":
            if not args:
                err: str = str(click.MissingParameter(f"Arguments missing. Usage /rag enable \\<0|1\\>"))
                cli_output.render_command(f"Error: {err}")
            else:
                SettingsCmd.set("askai.rag.enabled", to_bool(args[0]), announce=False)
                cli_output.render_command(f"RAG has been *{'en' if configs.is_rag else 'dis'}abled* !")
        case _:
            cli_output.render_command(f"`RAG` is {_format_toggle(configs.is_rag)}")
