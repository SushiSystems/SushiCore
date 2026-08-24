"""Rendering backends.

``Renderer`` is the seam the rest of the package depends on (DIP): the
:class:`~sushicore.console.Console` facade only ever talks to this Protocol,
never to Rich directly. Any object implementing these four methods is a
drop-in renderer (LSP) — swap in a plain-text renderer for CI logs, a JSON
renderer for machine consumption, etc., without touching Console or anything
that calls it.
"""

from __future__ import annotations

import sys
from typing import Protocol

from .theme import Theme


class Renderer(Protocol):
    """Minimal interface Console needs — nothing more (ISP)."""

    def line(self, style: str, prefix: str, message: str) -> None: ...

    def command(self, cmd_style: str, prefix_style: str, prefix: str, cmd: str) -> None: ...

    def header(self, title: str, style: str) -> None: ...

    def panel(self, title: str, body: str, border_style: str) -> None: ...

    @property
    def raw(self):
        """The underlying Rich ``Console``, for callers that render Rich objects
        directly (tables, pre-styled strings) instead of going through the
        semantic methods above. Always a real Rich console — even a no-color
        renderer routes through Rich so ``Table``/``Panel`` rendering keeps
        working, it just emits no ANSI codes.
        """
        ...


def _force_utf8_streams() -> None:
    # A legacy Windows console defaults to cp1252, which cannot encode Rich's
    # spinner glyphs (e.g. the braille '⠼'); the first such character would
    # raise UnicodeEncodeError and turn any progress display — including the
    # failure path — into a secondary traceback.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


class RichRenderer:
    """Colored output via Rich. ``no_color=True`` keeps Rich's full rendering
    (tables, panels, rules) but strips ANSI codes — used for NO_COLOR,
    ``color = "never"``, and non-TTY streams instead of a hand-rolled
    plain-text path, so callers that reach for ``.raw`` to print a ``Table``
    keep working no matter which color mode is active.
    """

    def __init__(self, theme: Theme, no_color: bool = False) -> None:
        from rich.console import Console as _RichConsole
        from rich.theme import Theme as _RichTheme

        _force_utf8_streams()
        self._console = _RichConsole(theme=_RichTheme(theme.as_rich_styles()), no_color=no_color)

    @property
    def raw(self):
        return self._console

    def line(self, style: str, prefix: str, message: str) -> None:
        lead = f"[{style}]{prefix}[/{style}] " if prefix else ""
        self._console.print(f"{lead}{message}")

    def command(self, cmd_style: str, prefix_style: str, prefix: str, cmd: str) -> None:
        lead = f"[{prefix_style}]{prefix}[/{prefix_style}] " if prefix else ""
        self._console.print(f"{lead}Executing: [{cmd_style}]{cmd}[/{cmd_style}]")

    def header(self, title: str, style: str) -> None:
        self._console.print()
        self._console.rule(f"[{style}]{title}")

    def panel(self, title: str, body: str, border_style: str) -> None:
        from rich.panel import Panel

        self._console.print(Panel(body, title=f"[{border_style}]{title}", border_style=border_style))


class PlainRenderer:
    """Hand-rolled plain-text renderer with no Rich dependency at all — for a
    context that wants output with zero markup interpretation (e.g. piping to
    a dumb log sink). Not used automatically for NO_COLOR/non-TTY; see
    ``RichRenderer(no_color=True)`` for that.
    """

    def __init__(self, stream=None) -> None:
        self._stream = stream or sys.stdout

    @property
    def raw(self):
        from rich.console import Console as _RichConsole

        return _RichConsole(no_color=True, file=self._stream)

    def _write(self, text: str) -> None:
        print(text, file=self._stream)

    def line(self, style: str, prefix: str, message: str) -> None:
        self._write(f"{prefix} {message}" if prefix else message)

    def command(self, cmd_style: str, prefix_style: str, prefix: str, cmd: str) -> None:
        lead = f"{prefix} " if prefix else ""
        self._write(f"{lead}Executing: {cmd}")

    def header(self, title: str, style: str) -> None:
        self._write("")
        rule = "-" * max(len(title), 3)
        self._write(f"{rule}\n{title}\n{rule}")

    def panel(self, title: str, body: str, border_style: str) -> None:
        self._write(f"--- {title} ---")
        self._write(body)
        self._write("-" * (len(title) + 8))
