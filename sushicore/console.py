"""The public-facing console facade.

Console only translates semantic calls (``info``, ``success``, ...) into
renderer calls using a theme and icon set (SRP) — it never picks colors or
formats output itself. It is assembled by :func:`build_console` via
dependency injection, so tests or a future backend can hand it any
``Renderer`` implementation without subclassing anything here.
"""

from __future__ import annotations

from .icons import IconSet
from .renderer import Renderer
from .theme import Theme


class Console:
    def __init__(self, renderer: Renderer, theme: Theme, icons: IconSet) -> None:
        self._renderer = renderer
        self._theme = theme
        self._icons = icons

    @property
    def console(self):
        """The underlying Rich ``Console`` — for printing a ``Table``/``Panel``
        or other Rich renderable directly, bypassing the semantic methods."""
        return self._renderer.raw

    @property
    def accent(self) -> str:
        """The theme's accent style — same one used by ``header()``. Callers
        building their own Rich renderables (e.g. ``Table(header_style=...)``)
        should use this instead of hardcoding a color, so they stay in sync
        with the configured theme."""
        return self._theme.header

    def info(self, msg: str) -> None:
        self._renderer.line(self._theme.info, self._icons.info, msg)

    def success(self, msg: str) -> None:
        self._renderer.line(self._theme.success, self._icons.success, msg)

    def warn(self, msg: str) -> None:
        self._renderer.line(self._theme.warn, self._icons.warn, msg)

    def error(self, msg: str) -> None:
        self._renderer.line(self._theme.error, self._icons.error, msg)

    def command(self, cmd: str) -> None:
        """Echo the command about to be executed."""
        self._renderer.command(self._theme.cmd, self._theme.info, self._icons.info, cmd)

    def header(self, title: str) -> None:
        self._renderer.header(title, self._theme.header)

    def fail_panel(self, title: str, body: str) -> None:
        self._renderer.panel(title, body, self._theme.panel_border)
