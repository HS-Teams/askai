#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.tui.header
      @file: app_header.py
   @created: Mon, 29 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.core.askai_configs import configs
from askai.core.component.multimedia.recorder import recorder
from askai.core.support.shared_instances import shared
from askai.tui.app_icons import AppIcons
from askai.tui.app_widgets import MenuIcon
from hspylib.core.zoned_datetime import now
from rich.text import Text
from textual.app import RenderResult
from textual.events import Mount
from textual.reactive import Reactive
from textual.widget import Widget
from textwrap import dedent


class Header(Widget):
    """A header widget with icon and notifications."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def notifications(self):
        return self.query_one(HeaderNotifications)

    @property
    def screen_title(self) -> str:
        """The title that this header will display."""
        screen_title = self.screen.title
        title = screen_title if screen_title is not None else self.app.title
        return title

    @property
    def screen_sub_title(self) -> str:
        """The sub-title that this header will display."""
        screen_sub_title = self.screen.sub_title
        sub_title = screen_sub_title if screen_sub_title is not None else self.app.sub_title
        return sub_title

    def compose(self):
        """Compose the Header Widget."""
        yield MenuIcon(AppIcons.EXIT.value, "Exit the application", self.app.exit)
        yield MenuIcon(AppIcons.TOC.value, "Show/Hide Table of Contents", self._show_toc)
        yield MenuIcon(AppIcons.CONSOLE.value, "Show console", self._show_console)
        yield MenuIcon(AppIcons.SETTINGS.value, "Show settings", self._show_settings)
        yield MenuIcon(AppIcons.INFO.value, "Show application information", self._show_info)
        yield MenuIcon(AppIcons.HELP.value, "Show application help", self._show_help)
        yield HeaderTitle()
        yield HeaderNotifications()

    def _on_mount(self, _: Mount) -> None:
        async def set_title() -> None:
            """The title that this header will display."""
            self.query_one(HeaderTitle).text = self.screen_title

        async def set_sub_title() -> None:
            """The sub-title that this header will display."""
            self.query_one(HeaderTitle).sub_text = self.screen_sub_title

        self.watch(self.app, "title", set_title)
        self.watch(self.app, "sub_title", set_sub_title)
        self.watch(self.screen, "title", set_title)
        self.watch(self.screen, "sub_title", set_sub_title)

    def _show_help(self) -> None:
        """Handle the header menu 'help' clicks."""
        self.app.help.set_class(False, "-hidden")
        self.app.info.set_class(True, "-hidden")
        self.app.md_console.set_class(True, "-hidden")
        self.app.settings.set_class(True, "-hidden")

    def _show_settings(self) -> None:
        """Handle the header menu 'settings' clicks."""
        self.app.settings.set_class(False, "-hidden")
        self.app.help.set_class(True, "-hidden")
        self.app.info.set_class(True, "-hidden")
        self.app.md_console.set_class(True, "-hidden")

    def _show_info(self) -> None:
        """Handle the header menu 'info' clicks."""
        self.app.info.set_class(False, "-hidden")
        self.app.help.set_class(True, "-hidden")
        self.app.md_console.set_class(True, "-hidden")
        self.app.settings.set_class(True, "-hidden")

    def _show_console(self) -> None:
        """Handle the header menu 'console' clicks."""
        self.app.activate_markdown()
        self.app.help.set_class(True, "-hidden")
        self.app.info.set_class(True, "-hidden")
        self.app.settings.set_class(True, "-hidden")

    def _show_toc(self) -> None:
        """Handle the header menu 'toc' clicks."""
        self.app.action_toggle_table_of_contents()
        self._show_console()


class HeaderTitle(Widget):
    """Display the title / subtitle in the header."""

    text = Reactive("")
    sub_text = Reactive("")

    def render(self) -> RenderResult:
        """Render the title and sub-title."""
        text = Text(self.text, no_wrap=True, overflow="ellipsis")
        if self.sub_text:
            text.append(f"  {AppIcons.SEPARATOR_H}  ")
            text.append(str(self.sub_text))
        return text


class HeaderNotifications(Widget):
    """Display a notification widget on the right of the header."""

    speaking = Reactive(configs.is_speak)
    assistive = Reactive(configs.is_assistive)
    debugging = Reactive(configs.is_debug)
    caching = Reactive(configs.is_cache)
    rag = Reactive(configs.is_rag)
    listening = Reactive(False)
    headphones = Reactive(False)
    idiom = Reactive(f"{configs.language.name} ({configs.language.idiom})")

    def __init__(self):
        super().__init__()
        self.tooltip = str(self)

    def __str__(self):
        device_info: str = f"{recorder.input_device[1]}" if recorder.input_device else "-"
        speech = shared.speech.tts
        voice: str = getattr(speech, 'voice_name', speech.voice)
        # fmt: off
        return dedent(f"""\
            Assistive: {'' if self.assistive else ''}
            Debugging: {'' if self.debugging else ''}
            Listening: {'' if self.listening else ''}
             Speaking: {'   ' + voice if self.speaking else ''}
              Caching: {'' if self.caching else ''}
                  RAG: {'' if self.rag else ''}
             Audio In: {device_info}
                Idiom: {AppIcons.GLOBE} {self.idiom}
            """).strip()
        # fmt: on

    def _on_mount(self, _: Mount) -> None:
        self.set_interval(1, callback=self.refresh, name="update clock")
        self.set_interval(0.5, callback=self.refresh_icons, name="update icons")

    def render(self) -> RenderResult:
        """Render the header notifications."""
        from askai.core.support.context_usage import context_label
        from askai.core.askai_messages import msg

        return Text(
            f"{AppIcons.HEADPHONES if self.headphones else AppIcons.BUILT_IN_SPEAKER}  "
            f"{AppIcons.LISTENING_ON if self.listening else AppIcons.LISTENING_OFF}  "
            f"{AppIcons.SPEAKING_ON if self.speaking else AppIcons.SPEAKING_OFF} "
            f"{AppIcons.ASSISTIVE_ON if self.assistive else AppIcons.ASSISTIVE_OFF}  "
            f"{AppIcons.CACHING_ON if self.caching else AppIcons.CACHING_OFF} "
            f"{AppIcons.DEBUG_ON if self.debugging else AppIcons.DEBUG_OFF}  "
            f"{AppIcons.SEPARATOR_V} {now(f'%a %d %b %X')} · {msg.t('Context')}: {context_label(shared.engine, msg.t)}",
            no_wrap=True,
            overflow="ellipsis",
        )

    def refresh_icons(self) -> None:
        """Update the application widgets."""
        self.headphones = recorder.is_headphones()
        self.assistive = configs.is_assistive
        self.debugging = configs.is_debug
        self.caching = configs.is_cache
        self.speaking = configs.is_speak
        self.idiom = f"{configs.language.name} ({configs.language.idiom})"
        self.app.info.info_text = str(self.app)
        self.app.settings.data = self.app.app_settings
        self.tooltip = str(self)

    async def watch_speaking(self) -> None:
        self.refresh()

    async def watch_debugging(self) -> None:
        self.refresh()

    async def watch_caching(self) -> None:
        self.refresh()

    async def watch_listening(self) -> None:
        self.refresh()

    async def watch_headphones(self) -> None:
        self.refresh()

    async def watch_idiom(self) -> None:
        self.refresh()
