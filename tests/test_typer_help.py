# test_typer_help.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""help_group draws every --help level as a HelpPage, or falls back to Typer's own."""

import io
import logging
import re

import pytest
import typer
import typer.main
from rich.console import Group, RenderableType
from rich.text import Text
from typer.testing import CliRunner

from sushicore.console import Console
from sushicore.icons import IconSet
from sushicore.renderer import PlainRenderer, TerminalMemoryRenderer
from sushicore.theme import Theme
from sushicore.typer_help import help_group
from sushicore.ui.logo import Logo
from tests.ui.capture import capture


pytestmark = pytest.mark.small

K_BLOCKS = "▀▄█"
K_ANSI = re.compile(r"\x1b\[[0-9;]*m")
K_TYPER_PANEL = "─ Options ─"
K_LOGGER_NAME = "sushicore.typer_help"
K_AMBER_CODE = "38;2;240;165;0"
K_NORI_CODE = "38;2;26;28;32"
K_FIRST_BLOCK = "the block that drew"
# Typer names the argument MODULE up to 0.20 and module from 0.27 on.
K_ARGUMENT_ROW = re.compile(r"^ +module\b", re.IGNORECASE | re.MULTILINE)


def _plain_console(stream: io.StringIO) -> Console:
    """Return a colourless Console whose Rich console writes to ``stream``."""
    return Console(PlainRenderer(stream=stream), Theme(), IconSet())


def _app(console: Console) -> typer.Typer:
    """Return the hub-like test app whose help draws on ``console``."""
    group = help_group(lambda: console)
    app = typer.Typer(cls=group, name="hub", help="Manage the stack.", rich_markup_mode="rich")
    gui = typer.Typer(cls=group, name="gui", help="The desktop application.")
    app.add_typer(gui, name="gui", rich_help_panel="Desktop app")

    @app.callback(invoke_without_command=True)
    def root(ctx: typer.Context):
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(0)

    @app.command("add", rich_help_panel="Modules", epilog="hub add sr  # bring sushiruntime in")
    def add(
        module: str = typer.Argument(..., help="The module."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Show the plan only."),
    ):
        """Bring a module in."""

    @app.command("doctor")
    def doctor():
        """Check tools."""

    @gui.command("build", epilog="hub gui build --type release")
    def build():
        """Build it."""

    return app


def _run(*args: str) -> str:
    """Return the page the console printed for ``args``, asserting the run exited zero."""
    stream = io.StringIO()
    result = CliRunner().invoke(_app(_plain_console(stream)), list(args))
    assert result.exit_code == 0, result.output
    return stream.getvalue()


def test_root_help_groups_commands_under_their_panels():
    out = _run("--help")
    assert "Modules" in out and "Desktop app" in out and "Commands" in out
    assert out.index("Modules") < out.index("  add") < out.index("Desktop app") < out.index("  gui")


def test_a_bare_invocation_prints_the_same_page():
    assert _run() == _run("--help")


def test_a_leaf_page_lists_its_arguments():
    out = _run("add", "--help")
    assert "Arguments" in out and K_ARGUMENT_ROW.search(out)


def test_a_leaf_page_lists_its_options():
    out = _run("add", "--help")
    assert "--dry-run" in out and "Show the plan only." in out


def test_a_leaf_page_lists_its_examples():
    out = _run("add", "--help")
    assert "Examples" in out and "hub add sr" in out and "bring sushiruntime in" in out


def test_a_leaf_page_shows_the_required_extra_typer_puts_on_a_parameter():
    assert "The module.  [required]" in _run("add", "--help")


def test_a_page_prints_no_escape_backslashes():
    assert "\\" not in _run("add", "--help")


def test_a_sub_group_draws_its_own_page_not_a_leaf_page():
    out = _run("gui", "--help")
    assert "build" in out and "Usage: hub gui" in out


def test_a_leaf_below_a_sub_group_draws_a_page():
    out = _run("gui", "build", "--help")
    assert "Usage: hub gui build" in out and "hub gui build --type release" in out


def test_a_command_with_no_panel_lands_under_commands():
    out = _run("--help")
    assert out.index("Commands") < out.index("  doctor")


def test_no_logo_on_a_console_that_is_not_a_terminal():
    assert not any(ch in _run("--help") for ch in K_BLOCKS)


def test_the_click_formatter_is_left_empty_for_a_page_drawing_group():
    result = CliRunner().invoke(_app(_plain_console(io.StringIO())), ["--help"])
    assert result.exit_code == 0, result.output
    assert result.output.strip() == ""


def test_the_provider_is_called_as_a_plain_function_not_bound_to_the_group():
    seen = []

    def provider():
        console = _plain_console(io.StringIO())
        seen.append(console)
        return console

    app = typer.Typer(cls=help_group(provider), name="hub", help="Manage the stack.")

    @app.command("add")
    def add():
        """Bring a module in."""

    @app.command("doctor")
    def doctor():
        """Check tools."""

    assert CliRunner().invoke(app, ["--help"]).exit_code == 0
    assert len(seen) == 1


def test_looking_a_child_up_twice_leaves_it_with_one_help_page():
    stream = io.StringIO()
    group = typer.main.get_command(_app(_plain_console(stream)))
    ctx = group.make_context("hub", [], resilient_parsing=True)
    first = group.get_command(ctx, "add")
    second = group.get_command(ctx, "add")
    assert first is second
    leaf_ctx = second.make_context("add", [], parent=ctx, resilient_parsing=True)
    assert second.get_help(leaf_ctx) == ""
    assert stream.getvalue().count("Usage: hub add") == 1


def _terminal_console(
    color_system: str,
    no_color: bool = False,
    width: int = 80,
    dark_background: bool = False,
    stream: io.StringIO | None = None,
) -> tuple[Console, TerminalMemoryRenderer]:
    """Return a Console on an in-memory terminal of the given shape, and its renderer."""
    renderer = TerminalMemoryRenderer(color_system, width=width, no_color=no_color, stream=stream)
    return Console(renderer, Theme(), IconSet(), dark_background=dark_background), renderer


def _two_commands(app: typer.Typer) -> typer.Typer:
    """Add the two commands every help-screen app in this file carries."""

    @app.command("add")
    def add():
        """Bring a module in."""

    @app.command("doctor")
    def doctor():
        """Check tools."""

    return app


def _terminal_page(*args: str, **shape) -> str:
    """Return what the in-memory terminal of shape ``shape`` printed while ``args`` ran."""
    console, renderer = _terminal_console(**shape)
    app = _two_commands(typer.Typer(cls=help_group(lambda: console), name="hub", help="Manage."))
    result = CliRunner().invoke(app, list(args))
    assert result.exit_code == 0, result.output
    return renderer.written()


def _shows_logo(output: str) -> bool:
    """Report whether the output holds a logo block character."""
    return any(ch in output for ch in K_BLOCKS)


def _block_rows(text: str) -> list[str]:
    """Return the rows of ``text`` that hold logo pixels, without colour codes or trailing space."""
    plain = K_ANSI.sub("", text)
    return [line.rstrip() for line in plain.split("\n") if _shows_logo(line)]


def _drawn_alone(logo: Logo, width: int) -> list[str]:
    """Return the rows of ``logo`` drawn by itself at ``width`` columns."""
    return _block_rows(capture(logo, width=width))


def _root_lines() -> tuple[list[str], list[int]]:
    """Return the root page's lines on a wide dark terminal and the indices of the logo rows."""
    output = _terminal_page("--help", color_system="truecolor", width=90, dark_background=True)
    lines = K_ANSI.sub("", output).split("\n")
    return lines, [i for i, line in enumerate(lines) if _shows_logo(line)]


@pytest.mark.parametrize("color_system", ["256", "truecolor"])
def test_the_root_page_shows_the_logo_on_a_terminal_with_256_colours_or_more(color_system):
    assert _shows_logo(_terminal_page("--help", color_system=color_system))


def test_the_page_reaches_a_truecolour_terminal_with_the_rolls_own_colour_codes():
    output = _terminal_page("--help", color_system="truecolor")
    assert K_AMBER_CODE in output and K_NORI_CODE in output


def test_the_root_page_leaves_one_blank_line_above_the_logo():
    lines, rows = _root_lines()
    assert lines[: rows[0]] == [""]


def test_the_root_page_leaves_two_blank_lines_below_the_logo_before_the_title():
    lines, rows = _root_lines()
    assert lines[rows[-1] + 1 : rows[-1] + 3] == ["", ""]
    assert lines[rows[-1] + 3].strip() == "hub"


def test_a_dark_terminal_draws_the_lockup_with_its_glow():
    logo = Logo(glow=True)
    output = _terminal_page(
        "--help", color_system="truecolor", width=logo.width, dark_background=True
    )
    assert _block_rows(output) == _drawn_alone(logo, logo.width)


def test_a_light_terminal_draws_the_lockup_without_a_glow():
    logo = Logo(glow=False)
    output = _terminal_page("--help", color_system="truecolor", width=logo.width)
    assert _block_rows(output) == _drawn_alone(logo, logo.width)


def test_a_console_too_narrow_for_the_wordmark_draws_the_mark_alone():
    mark = Logo(wordmark=False, glow=False)
    output = _terminal_page("--help", color_system="truecolor", width=mark.width)
    assert _block_rows(output) == _drawn_alone(mark, mark.width)


def test_a_console_narrower_than_the_mark_draws_no_logo():
    width = Logo(wordmark=False, glow=False).width - 1
    assert not _shows_logo(_terminal_page("--help", color_system="truecolor", width=width))


def test_a_leaf_page_does_not_show_the_logo_on_a_colour_terminal():
    assert not _shows_logo(_terminal_page("add", "--help", color_system="truecolor"))


def test_the_root_page_hides_the_logo_on_a_standard_colour_terminal():
    assert not _shows_logo(_terminal_page("--help", color_system="standard"))


def test_the_root_page_hides_the_logo_when_colour_is_switched_off_on_a_terminal():
    assert not _shows_logo(_terminal_page("--help", color_system="truecolor", no_color=True))


class _LegacyEncodingStream(io.StringIO):
    """An in-memory stream that reports a legacy code page, as a Windows console can."""

    encoding = "cp1252"


def test_the_root_page_hides_the_logo_on_a_console_whose_encoding_is_not_utf():
    console, renderer = _terminal_console("truecolor", stream=_LegacyEncodingStream())
    app = _two_commands(typer.Typer(cls=help_group(lambda: console), name="hub", help="Manage."))
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0, result.output
    assert renderer.written() != "" and not _shows_logo(renderer.written())


class _RecordedWarnings(logging.Handler):
    """Keeps the message of every warning it receives."""

    def __init__(self) -> None:
        """Start with no message."""
        super().__init__(logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Keep the formatted message of ``record``."""
        self.messages.append(record.getMessage())


def _recording_logger() -> tuple[logging.Logger, _RecordedWarnings]:
    """Return a logger of its own, outside the process-wide tree, and the handler that records it."""
    logger = logging.Logger(K_LOGGER_NAME, logging.WARNING)
    handler = _RecordedWarnings()
    logger.addHandler(handler)
    return logger, handler


def _guarded_app(provider, logger, help_text: str = "Manage the stack.", **options) -> typer.Typer:
    """Return a two-command app whose help draws through ``provider`` and logs to ``logger``."""
    app = typer.Typer(cls=help_group(provider, logger), name="hub", help=help_text, **options)
    return _two_commands(app)


@pytest.mark.parametrize("args", [("--help",), ("add", "--help")], ids=["group", "child"])
def test_a_provider_that_raises_falls_back_to_typers_help_with_one_warning(args):
    def provider():
        raise RuntimeError("no workspace here")

    logger, warnings = _recording_logger()
    result = CliRunner().invoke(_guarded_app(provider, logger), list(args))
    assert result.exit_code == 0, result.output
    assert K_TYPER_PANEL in K_ANSI.sub("", result.output)
    assert len(warnings.messages) == 1 and "no workspace here" in warnings.messages[0]


def test_a_help_group_used_without_a_provider_falls_back_to_typers_help():
    logger, warnings = _recording_logger()
    app = _two_commands(typer.Typer(cls=help_group(None, logger), name="hub", help="Manage."))
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0, result.output
    assert K_TYPER_PANEL in K_ANSI.sub("", result.output)
    assert len(warnings.messages) == 1


def _stray_close_tag_run():
    """Run --help on an app whose help text holds a stray close tag; return the result and warnings."""
    console = _plain_console(io.StringIO())
    logger, warnings = _recording_logger()
    app = _guarded_app(lambda: console, logger, "Manage [/] the stack.", rich_markup_mode="rich")
    return CliRunner().invoke(app, ["--help"]), warnings.messages


def test_a_stray_close_tag_in_rich_help_is_logged():
    _, messages = _stray_close_tag_run()
    assert "MarkupError" in messages[0]


def test_a_stray_close_tag_in_rich_help_falls_back_to_typers_help_without_raising():
    result, _ = _stray_close_tag_run()
    assert result.exit_code == 0, result.exception
    assert "Manage [/] the stack." in K_ANSI.sub("", result.output)


def test_each_help_call_logs_one_warning_of_its_own():
    def provider():
        raise RuntimeError("no workspace here")

    logger, warnings = _recording_logger()
    app = _guarded_app(provider, logger)
    CliRunner().invoke(app, ["--help"])
    CliRunner().invoke(app, ["add", "--help"])
    assert len(warnings.messages) == 2


class _Exploding:
    """Raises while Rich draws it, after the block before it has drawn."""

    def __rich_console__(self, console, options):
        """Raise instead of yielding segments."""
        raise RuntimeError("the second block cannot be drawn")


class _HalfDrawnLogo:
    """A logo whose first block draws and whose second block raises."""

    def render(self, theme: Theme) -> RenderableType:
        """Return a block that draws and, after it, a block that raises."""
        return Group(Text(K_FIRST_BLOCK), _Exploding())


def test_a_block_that_fails_to_draw_leaves_no_part_of_the_page_on_the_console():
    console, renderer = _terminal_console("truecolor")
    logger, warnings = _recording_logger()
    group = help_group(lambda: console, logger, lambda **shape: _HalfDrawnLogo())
    app = _two_commands(typer.Typer(cls=group, name="hub", help="Manage."))
    result = CliRunner().invoke(app, ["--help"])
    assert renderer.written() == ""
    assert K_FIRST_BLOCK not in result.output and K_TYPER_PANEL in K_ANSI.sub("", result.output)
    assert len(warnings.messages) == 1
