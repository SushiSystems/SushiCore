"""The public-facing console facade.

Console only translates semantic calls (``info``, ``success``, ``table``, ...)
into renderer calls using a theme and icon set; it never picks colors or
formats output itself. :func:`sushicore.build_console` assembles it, so tests
or another backend can hand it any ``Renderer`` without subclassing.
"""

from __future__ import annotations

from .icons import IconSet
from .renderer import Renderer
from .theme import Theme


class Console:
    """Translate semantic calls into renderer calls with a theme and an icon set."""

    def __init__(
        self,
        renderer: Renderer,
        theme: Theme,
        icons: IconSet,
        dark_background: bool = False,
    ) -> None:
        """Bind the renderer, theme and icon set this console speaks through.

        Args:
            dark_background: What the caller decided about the terminal's background;
                this console never reads the environment to find out.
        """
        self._renderer = renderer
        self._theme = theme
        self._icons = icons
        self._dark_background = dark_background
        self._prompt_count = 0

    @property
    def console(self):
        """Return the underlying Rich ``Console`` for printing a Rich renderable directly."""
        return self._renderer.raw

    @property
    def accent(self) -> str:
        """Return the theme's header style, for callers building their own Rich renderables."""
        return self._theme.header

    @property
    def theme(self) -> Theme:
        """Return the theme this console styles its output with."""
        return self._theme

    @property
    def dark_background(self) -> bool:
        """Return whether the terminal this console writes to has a dark background."""
        return self._dark_background

    def info(self, msg: str) -> None:
        """Print an informational line."""
        self._renderer.line(self._theme.info, self._icons.info, msg)

    def success(self, msg: str) -> None:
        """Print a success line."""
        self._renderer.line(self._theme.success, self._icons.success, msg)

    def warn(self, msg: str) -> None:
        """Print a warning line."""
        self._renderer.line(self._theme.warn, self._icons.warn, msg)

    def error(self, msg: str) -> None:
        """Print an error line."""
        self._renderer.line(self._theme.error, self._icons.error, msg)

    def command(self, cmd: str) -> None:
        """Echo the command about to be executed."""
        self._renderer.command(self._theme.cmd, self._theme.info, self._icons.info, cmd)

    def header(self, title: str) -> None:
        """Print a section header."""
        self._renderer.header(title, self._theme.header)

    def fail_panel(self, title: str, body: str) -> None:
        """Print a failure body inside a bordered panel."""
        self._renderer.panel(title, body, self._theme.panel_border)

    def table(self, columns: list[str], rows: list[list[str]], title: str = "") -> None:
        """Print a table of string cells with the theme's header style."""
        self._renderer.table(title, columns, rows, self._theme.header)

    def progress(self, label: str, index: int, count: int, fraction: float | None = None) -> None:
        """Report step ``index`` of ``count`` for ``label``, with a fraction when known."""
        self._renderer.progress(label, index, count, fraction)

    def result(self, ok: bool, payload: dict | None = None) -> None:
        """Report the command's outcome and its payload, an empty dict when none is given."""
        self._renderer.result(ok, {} if payload is None else payload)

    def prompt(self, message: str, default: str | None = None) -> str:
        """Ask a question under an id ``prompt-N`` counted per instance and return the answer."""
        self._prompt_count += 1
        return self._renderer.prompt(f"prompt-{self._prompt_count}", message, default)
