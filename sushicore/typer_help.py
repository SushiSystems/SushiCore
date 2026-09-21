"""Wires the help page into Typer; the only module in sushicore that imports Typer.

The group replaces each child's format_help as it hands the child out; the reason is in
docs/agent/specs/2026-09-21-terminal-components-design.md.
"""

from __future__ import annotations

import io
import logging
from functools import partial
from typing import Any, Callable, ClassVar

import click
from rich.console import Console as RichConsole
from typer.core import TyperGroup

from .console import Console
from .help.from_click import build_model
from .help.logo_choice import choose_logo
from .help.page import HelpPage
from .theme import Theme
from .ui.logo import Logo

K_LOGO_COLOUR_SYSTEMS = ("256", "truecolor")
K_LOGGER = logging.getLogger("sushicore.help")

Provider = Callable[[], Console]
HelpWriter = Callable[[click.Context, click.HelpFormatter], None]


class _HelpPageError(Exception):
    """Reports that a help page cannot be drawn."""


class HelpGroup(TyperGroup):
    """Draws its own help, and its children's, as a HelpPage."""

    console_provider: ClassVar[Provider | None] = None
    draws_help_page: ClassVar[bool] = True

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Write this group's help page into the formatter, or Typer's help when it cannot."""
        _write_guarded(
            self, ctx, formatter, self.console_provider, partial(TyperGroup.format_help, self)
        )

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Return the child command, its help redirected to the page unless it draws its own."""
        command = super().get_command(ctx, cmd_name)
        if command is not None and not getattr(command, "draws_help_page", False):
            command.format_help = _page_writer(command, self.console_provider)
        return command


def help_group(console: Provider) -> type[HelpGroup]:
    """Return a HelpGroup subclass that draws with the console ``console()`` returns."""
    return type("SushiGroup", (HelpGroup,), {"console_provider": staticmethod(console)})


def _page_writer(command: Any, provider: Provider | None) -> HelpWriter:
    """Return the format_help that draws ``command`` as a page on the provider's console."""

    def format_help(ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Write the command's help page into the formatter, or Typer's help when it cannot."""
        _write_guarded(
            command, ctx, formatter, provider, partial(type(command).format_help, command)
        )

    return format_help


def _write_guarded(
    command: Any,
    ctx: click.Context,
    formatter: click.HelpFormatter,
    provider: Provider | None,
    typer_help: HelpWriter,
) -> None:
    """Write ``command``'s page, or log one warning and let Typer write its own help instead."""
    try:
        if provider is None:
            raise _HelpPageError("the help group was built without a console provider")
        _write_page(command, ctx, formatter, provider())
    except Exception as error:
        K_LOGGER.warning(
            "the help page for %s was not drawn (%s: %s); Typer's own help is used instead",
            ctx.command_path,
            type(error).__name__,
            error,
        )
        typer_help(ctx, formatter)


def _write_page(
    command: Any,
    ctx: click.Context,
    formatter: click.HelpFormatter,
    console: Console,
) -> None:
    """Build the page for ``command`` and write it, drawn for ``console``, into ``formatter``."""
    raw = console.console
    page = HelpPage(build_model(command, ctx), logo=_logo_for(raw, console.dark_background))
    # The page is drawn in full before the single write.
    formatter.write(_draw(page, console.theme, raw))


def _logo_for(raw: RichConsole, dark_background: bool) -> Logo | None:
    """Return the logo this console can show, or None when it can show none."""
    if not _logo_visible(raw):
        return None
    return choose_logo(width=raw.width, dark_background=dark_background)


def _logo_visible(raw: RichConsole) -> bool:
    """Report whether the console can show the logo: a UTF-8 terminal with 256 colours or more."""
    return (
        raw.is_terminal
        and not raw.no_color
        and raw.color_system in K_LOGO_COLOUR_SYSTEMS
        and raw.encoding.lower().startswith("utf")
    )


def _draw(page: HelpPage, theme: Theme, raw: RichConsole) -> str:
    """Return the page as text shaped like ``raw``: its width, colour system and colour setting."""
    target = RichConsole(
        file=io.StringIO(),
        width=raw.width,
        force_terminal=raw.is_terminal,
        color_system=raw.color_system,
        no_color=raw.no_color,
        legacy_windows=False,
        highlight=False,
    )
    target.print(page.render(theme))
    return target.file.getvalue()
