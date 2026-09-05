"""Rendering backends.

``Renderer`` is the seam the rest of the package depends on: the
:class:`~sushicore.console.Console` facade only ever talks to this Protocol,
never to Rich directly. Any object implementing its eight methods is a
drop-in renderer. Three ship here: ``RichRenderer`` for a terminal,
``PlainRenderer`` for markup-free text, and ``JsonRenderer`` for one event
per line on stdout, the shape ``docs/agent/specs/2026-09-05-hub-design.md``
section 7 fixes.
"""

from __future__ import annotations

import sys
from typing import Protocol

from .theme import Theme


class Renderer(Protocol):
    """The interface Console needs and nothing more."""

    def line(self, style: str, prefix: str, message: str) -> None:
        """Draw one prefixed message."""
        ...

    def command(self, cmd_style: str, prefix_style: str, prefix: str, cmd: str) -> None:
        """Echo a command about to run."""
        ...

    def header(self, title: str, style: str) -> None:
        """Draw a section header."""
        ...

    def panel(self, title: str, body: str, border_style: str) -> None:
        """Draw a bordered block of text under a title."""
        ...

    def table(self, title: str, columns: list[str], rows: list[list[str]], header_style: str) -> None:
        """Draw a table of string cells under a title."""
        ...

    def progress(self, label: str, index: int, count: int, fraction: float | None) -> None:
        """Report step ``index`` of ``count`` for ``label``, with a fraction when known."""
        ...

    def result(self, ok: bool, payload: dict) -> None:
        """Report the command's outcome and its structured payload."""
        ...

    def prompt(self, prompt_id: str, message: str, default: str | None) -> str:
        """Ask a question and return the answer, or ``default or ""`` on an empty answer or EOF."""
        ...

    @property
    def raw(self):
        """Return the underlying Rich ``Console`` for callers that render Rich objects directly."""
        ...


def _force_utf8_streams() -> None:
    """Reconfigure stdout and stderr to UTF-8 so Rich glyphs never raise on a legacy console."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def _answer(raw: str | None, default: str | None) -> str:
    """Return the stripped answer, or ``default or ""`` when the answer is empty or missing."""
    text = (raw or "").strip()
    return text if text else (default or "")


def _progress_text(label: str, index: int, count: int, fraction: float | None) -> str:
    """Format a progress step as ``[label] index/count`` plus a percentage when known."""
    text = f"[{label}] {index}/{count}"
    if fraction is not None:
        text += f" ({fraction * 100:.0f}%)"
    return text


class RichRenderer:
    """Render through Rich; ``no_color=True`` keeps the layout and strips the ANSI codes."""

    def __init__(self, theme: Theme, no_color: bool = False) -> None:
        """Build the Rich console with the theme's styles registered."""
        from rich.console import Console as _RichConsole
        from rich.theme import Theme as _RichTheme

        _force_utf8_streams()
        self._console = _RichConsole(theme=_RichTheme(theme.as_rich_styles()), no_color=no_color)

    @property
    def raw(self):
        """Return the Rich console this renderer prints through."""
        return self._console

    def line(self, style: str, prefix: str, message: str) -> None:
        """Print the message behind a styled prefix."""
        lead = f"[{style}]{prefix}[/{style}] " if prefix else ""
        self._console.print(f"{lead}{message}")

    def command(self, cmd_style: str, prefix_style: str, prefix: str, cmd: str) -> None:
        """Print ``Executing:`` and the styled command."""
        lead = f"[{prefix_style}]{prefix}[/{prefix_style}] " if prefix else ""
        self._console.print(f"{lead}Executing: [{cmd_style}]{cmd}[/{cmd_style}]")

    def header(self, title: str, style: str) -> None:
        """Print a blank line and a titled rule."""
        self._console.print()
        self._console.rule(f"[{style}]{title}")

    def panel(self, title: str, body: str, border_style: str) -> None:
        """Print the body inside a Rich ``Panel``."""
        from rich.panel import Panel

        self._console.print(Panel(body, title=f"[{border_style}]{title}", border_style=border_style))

    def table(self, title: str, columns: list[str], rows: list[list[str]], header_style: str) -> None:
        """Print the rows as a Rich ``Table``."""
        from rich.table import Table

        table = Table(title=title or None, header_style=header_style)
        for column in columns:
            table.add_column(column)
        for row in rows:
            table.add_row(*row)
        self._console.print(table)

    def progress(self, label: str, index: int, count: int, fraction: float | None) -> None:
        """Print ``[label] index/count`` and a percentage when the fraction is known."""
        self._console.print(_progress_text(label, index, count, fraction), markup=False)

    def result(self, ok: bool, payload: dict) -> None:
        """Print nothing; the lines already told the reader the outcome."""

    def prompt(self, prompt_id: str, message: str, default: str | None) -> str:
        """Ask through ``rich.prompt.Prompt`` and return the answer."""
        from rich.prompt import Prompt

        try:
            answer = Prompt.ask(message, default=default, console=self._console)
        except EOFError:
            answer = None
        return _answer(answer, default)


class PlainRenderer:
    """Render as plain text with no markup interpretation."""

    def __init__(self, stream=None) -> None:
        """Write to ``stream``, or to stdout when none is given."""
        self._stream = stream or sys.stdout

    @property
    def raw(self):
        """Return a colourless Rich console bound to this renderer's stream."""
        from rich.console import Console as _RichConsole

        return _RichConsole(no_color=True, file=self._stream)

    def _write(self, text: str) -> None:
        """Print one line to the stream."""
        print(text, file=self._stream)

    def line(self, style: str, prefix: str, message: str) -> None:
        """Print the prefix and the message separated by one space."""
        self._write(f"{prefix} {message}" if prefix else message)

    def command(self, cmd_style: str, prefix_style: str, prefix: str, cmd: str) -> None:
        """Print ``Executing:`` and the command."""
        lead = f"{prefix} " if prefix else ""
        self._write(f"{lead}Executing: {cmd}")

    def header(self, title: str, style: str) -> None:
        """Print the title between two rules of dashes."""
        self._write("")
        rule = "-" * max(len(title), 3)
        self._write(f"{rule}\n{title}\n{rule}")

    def panel(self, title: str, body: str, border_style: str) -> None:
        """Print the body between a titled rule and a closing rule."""
        self._write(f"--- {title} ---")
        self._write(body)
        self._write("-" * (len(title) + 8))

    def table(self, title: str, columns: list[str], rows: list[list[str]], header_style: str) -> None:
        """Print the title, a header row and the rows, cells joined by two spaces."""
        if title:
            self._write(title)
        self._write("  ".join(columns))
        for row in rows:
            self._write("  ".join(row))

    def progress(self, label: str, index: int, count: int, fraction: float | None) -> None:
        """Print ``[label] index/count`` and a percentage when the fraction is known."""
        self._write(_progress_text(label, index, count, fraction))

    def result(self, ok: bool, payload: dict) -> None:
        """Print nothing; the lines already told the reader the outcome."""

    def prompt(self, prompt_id: str, message: str, default: str | None) -> str:
        """Ask through ``input()`` and return the answer."""
        suffix = f" [{default}]" if default else ""
        try:
            answer = input(f"{message}{suffix}: ")
        except EOFError:
            answer = None
        return _answer(answer, default)
