"""Reusable keyboard confirmation with explicit permission scope."""
from rich.panel import Panel
from rich.text import Text


def read_confirmation_key(_prompt=''):
    from hspylib.modules.cli.keyboard import Keyboard
    key = Keyboard.wait_keystroke()
    return key.val if key is not None else None


def show_confirmation(console, message: str, translate=lambda text: text, grants=()) -> None:
    body = Text(message)
    if grants:
        body.append('\n' + '\n'.join(grants), style='grey70')
    body.append('\n\n(1) ' + translate('Yes, allow'), style='bold green')
    body.append('     [(2) ' + translate('No, cancel') + ']', style='bold red')
    body.append('\n' + translate('This action only. Enter cancels.'), style='dim')
    console.print(Panel(body, title='⚠ ' + translate('CONFIRMATION REQUIRED'), border_style='yellow'))


class Confirmation:
    def __init__(self, read, show, translate=lambda text: text, echo=lambda text: None):
        self._read, self._show = read, show
        self._translate = translate
        self._echo = echo

    def __call__(self, message: str, grants=()) -> bool:
        if grants:
            self._show(message, grants=grants)
        else:
            self._show(message)
        labels = {True: self._translate('Yes, allow'), False: self._translate('No, cancel')}
        while True:
            answer = self._read('')
            if answer == '1':
                self._echo(labels[True])
                return True
            if answer in ('2', '\r', '\n', '\x1b', '', None):
                self._echo(labels[False])
                return False
