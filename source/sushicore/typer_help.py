# typer_help.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Wires the help page into Typer; the only module in sushicore that imports Typer.

The group replaces each child's format_help as it hands the child out; the reason is in
the terminal components design spec in the version history. A command that draws a
page prints it on the Rich console while get_help runs, so ctx.get_help() gives back an
empty string.
"""

from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, ClassVar

from rich.console import Console as RichConsole
from typer.core import TyperGroup

from .console import Console
from .help.from_click import build_model
from .help.logo_choice import choose_logo
from .help.page import HelpPage
from .ui.component import Component

if TYPE_CHECKING:
    import click

K_LOGO_COLOUR_SYSTEMS = ("256", "truecolor")
_log = logging.getLogger(__name__)

Provider = Callable[[], Console]
LogoChooser = Callable[..., Component | None]
HelpWriter = Callable[["click.Context", "click.HelpFormatter"], None]


class _HelpPageError(Exception):
    """Reports that a help page cannot be drawn."""


class HelpGroup(TyperGroup):
    """Draws its own help, and its children's, as a HelpPage."""

    console_provider: ClassVar[Provider | None] = None
    #: Receives the warnings a page that was not drawn leaves behind.
    help_logger: ClassVar[logging.Logger] = _log
    #: Called with ``width`` and ``dark_background``; returns the logo the root page shows, or None.
    logo_chooser: ClassVar[LogoChooser] = staticmethod(choose_logo)
    draws_help_page: ClassVar[bool] = True

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Print this group's help page, or write Typer's help into the formatter instead."""
        _write_guarded(self, ctx, formatter, self, partial(TyperGroup.format_help, self))

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Return the child command, its help redirected to the page unless it draws its own."""
        command = super().get_command(ctx, cmd_name)
        if command is not None and not getattr(command, "draws_help_page", False):
            command.format_help = _page_writer(command, self)
        return command


def help_group(
    console: Provider,
    logger: logging.Logger | None = None,
    logo_chooser: LogoChooser | None = None,
) -> type[HelpGroup]:
    """Return a HelpGroup subclass that draws with the console ``console()`` returns.

    Args:
        console: Returns the console a page is drawn on.
        logger: Receives the warnings of a page that was not drawn; this module's logger when None.
        logo_chooser: Picks the logo of the root page from ``width`` and ``dark_background``;
            :func:`~sushicore.help.logo_choice.choose_logo` when None.
    """
    attributes: dict[str, Any] = {"console_provider": staticmethod(console)}
    if logger is not None:
        attributes["help_logger"] = logger
    if logo_chooser is not None:
        attributes["logo_chooser"] = staticmethod(logo_chooser)
    return type("SushiGroup", (HelpGroup,), attributes)


def _page_writer(command: Any, group: HelpGroup) -> HelpWriter:
    """Return the format_help that draws ``command`` as a page, set up as ``group`` is."""

    def format_help(ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Print the command's help page, or write Typer's help into the formatter instead."""
        _write_guarded(command, ctx, formatter, group, partial(type(command).format_help, command))

    return format_help


def _write_guarded(
    command: Any,
    ctx: click.Context,
    formatter: click.HelpFormatter,
    group: HelpGroup,
    typer_help: HelpWriter,
) -> None:
    """Print ``command``'s page, or log one warning and let Typer write its own help instead."""
    log = group.help_logger
    try:
        if group.console_provider is None:
            raise _HelpPageError("the help group was built without a console provider")
        _print_page(command, ctx, group.console_provider(), group.logo_chooser)
    except Exception as error:
        log.warning(
            "the help page for %s was not drawn (%s: %s); Typer's own help is used instead",
            ctx.command_path,
            type(error).__name__,
            error,
        )
        _write_typer_or_plain(command, ctx, formatter, typer_help, log)


def _write_typer_or_plain(
    command: Any,
    ctx: click.Context,
    formatter: click.HelpFormatter,
    typer_help: HelpWriter,
    log: logging.Logger,
) -> None:
    """Let Typer write its help, or Click's plain help when Typer's fails, so help never crashes."""
    try:
        typer_help(ctx, formatter)
    except Exception as error:
        log.warning(
            "Typer's help for %s failed too (%s: %s); Click's plain help is used instead",
            ctx.command_path,
            type(error).__name__,
            error,
        )
        _click_format_help(command)(command, ctx, formatter)


def _click_format_help(command: Any) -> Callable[[Any, "click.Context", "click.HelpFormatter"], None]:
    """Return Click's own format_help for *command*, from Click or the copy Typer ships, whichever it uses."""
    for klass in type(command).__mro__:
        if klass.__module__.endswith("click.core") and "format_help" in vars(klass):
            return vars(klass)["format_help"]
    raise TypeError(f"{type(command).__name__} has no Click format_help in its bases")


def _print_page(
    command: Any, ctx: click.Context, console: Console, logo_chooser: LogoChooser
) -> None:
    """Build the page for ``command`` and print it on ``console``, leaving Click's formatter be."""
    raw = console.console
    page = HelpPage(build_model(command, ctx), logo=_logo_for(raw, console.dark_background, logo_chooser))
    # Rich draws the whole renderable before it writes, so a failure here leaves no half page.
    raw.print(page.render(console.theme))


def _logo_for(
    raw: RichConsole, dark_background: bool, logo_chooser: LogoChooser
) -> Component | None:
    """Return the logo this console can show, or None when it can show none."""
    if not _logo_visible(raw):
        return None
    return logo_chooser(width=raw.width, dark_background=dark_background)


def _logo_visible(raw: RichConsole) -> bool:
    """Report whether the console can show the logo: a UTF-8 terminal with 256 colours or more."""
    return (
        raw.is_terminal
        and not raw.no_color
        and raw.color_system in K_LOGO_COLOUR_SYSTEMS
        and raw.encoding.lower().startswith("utf")
    )
