"""Reusable explicit confirmation, independent of agents and application state."""

from rich.panel import Panel
from rich.text import Text


def show_confirmation(console, message: str, translate=lambda text: text) -> None:
    body = Text(message)
    body.append("\n\n(1) " + translate("Yes, allow"), style="bold green")
    body.append("     [(2) " + translate("No, cancel") + "]", style="bold red")
    body.append("\n" + translate("This action only. Enter cancels."), style="dim")
    console.print(
        Panel(
            body, title="⚠ " + translate("CONFIRMATION REQUIRED"), border_style="yellow"
        )
    )


class Confirmation:
    """Read a deliberate yes/no decision through caller-owned UI adapters."""

    def __init__(self, read, show, translate=lambda text: text):
        self._read, self._show = read, show
        self._translate = translate

    def __call__(self, message: str) -> bool:
        self._show(message)
        while True:
            answer = (
                (self._read(
                    "(1) " + self._translate("Yes, allow")
                    + "     [(2) " + self._translate("No, cancel") + "]"
                ) or "")
                .strip()
                .casefold()
                .rstrip(".!?")
            )
            if answer in {
                "1",
                "sim",
                "s",
                "yes",
                "y",
                self._translate("Yes").strip().casefold(),
            }:
                return True
            if answer in {
                "2",
                "não",
                "nao",
                "n",
                "no",
                "cancelar",
                "cancel",
                "",
                self._translate("No").strip().casefold(),
            }:
                return False
            self._show(
                self._translate(
                    "Choose (1) Yes or (2) No. No action has been authorized."
                )
                + "\n\n"
                + message
            )
