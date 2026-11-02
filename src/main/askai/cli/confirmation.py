"""Reusable keyboard confirmation with explicit permission scope."""
from rich.panel import Panel
from rich.text import Text


def read_confirmation_key(allowed='12ysn'):
    from hspylib.modules.cli.keyboard import Keyboard
    from askai.core.askai_prompt import prompt
    from askai.core.support.text_formatter import text_formatter
    text_formatter.console.print(Text(f'  {prompt.user.title()}: '), end='')
    while True:
        key = Keyboard.wait_keystroke()
        value = key.val.casefold() if key is not None else None
        if value in ('\r', '\n', '\x1b', '', None) or value in allowed:
            return value


def show_confirmation(console, message: str, translate=lambda text: text, grants=()) -> None:
    body = Text(message)
    if grants:
        body.append('\n' + '\n'.join(grants), style='grey70')
    body.append('\n\n(1) ' + translate('Yes, allow'), style='bold green')
    body.append('     [(2) ' + translate('No, cancel') + ']', style='bold red')
    if grants:
        body.append('     (3) ' + translate('Always'), style='bold green')
        body.append('     (4) ' + translate('Never'), style='bold red')
        body.append('     (5) ' + translate('Ask'), style='yellow')
    hint = ('Yes/No: this action only. Always/Never/Ask: save permission. Enter cancels.'
            if grants else 'This action only. Enter cancels.')
    body.append('\n' + translate(hint), style='yellow')
    console.print(Panel(body, title='⚠ ' + translate('CONFIRMATION REQUIRED'), border_style='yellow'))


def save_grants(names, value):
    from askai.core.askai_settings import settings
    from askai.core.permissions.grants import grant_key, validate_setting
    keys = [grant_key(name) for name in names]
    for key in keys:
        settings.put(key, validate_setting(key, value))


class Confirmation:
    def __init__(self, read, show, translate=lambda text: text, echo=lambda text: None,
                 save=save_grants):
        self._read, self._show = read, show
        self._translate = translate
        self._echo = echo
        self._save = save

    def __call__(self, message: str, grants=()) -> bool:
        if grants:
            self._show(message, grants=grants)
        else:
            self._show(message)
        labels = {True: self._translate('Yes, allow'), False: self._translate('No, cancel')}
        while True:
            answer = self._read('12345ysn' if grants else '12ysn')
            answer = answer.casefold() if isinstance(answer, str) else answer
            if grants and answer in {'3', '4', '5'}:
                value, label = {'3': ('allow', 'Always'), '4': ('never', 'Never'),
                                '5': ('ask', 'Ask')}[answer]
                self._save(grants, value)
                self._echo(self._translate(label))
                if answer == '5':
                    continue
                return answer == '3'
            if answer in ('1', 'y', 's'):
                self._echo(labels[True])
                return True
            if answer in ('2', 'n', '\r', '\n', '\x1b', '', None):
                self._echo(labels[False])
                return False
