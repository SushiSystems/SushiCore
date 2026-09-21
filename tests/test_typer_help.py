"""help_group draws every --help level as a HelpPage, or falls back to Typer's own."""

import io
import logging
import re

import click
import pytest
import typer
import typer.main
from rich.console import Console as RichConsole
from rich.errors import MarkupError
from typer.testing import CliRunner

from sushicore.console import Console
from sushicore.icons import IconSet
from sushicore.renderer import PlainRenderer
from sushicore.theme import Theme
from sushicore.typer_help import HelpGroup, help_group
from sushicore.ui.logo import Logo
from tests.ui.capture import capture

K_BLOCKS = "▀▄█"
K_ANSI = re.compile(r"\x1b\[[0-9;]*m")
K_TYPER_PANEL = "─ Options ─"
K_LOGGER_NAME = "sushicore.help"


def _app() -> typer.Typer:
    """Return the hub-like test app whose help draws through the page."""
    console = Console(PlainRenderer(stream=io.StringIO()), Theme(), IconSet())
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
    """Return the output of one CliRunner invocation, asserting it exited zero."""
    result = CliRunner().invoke(_app(), list(args))
    assert result.exit_code == 0, result.output
    return result.output


def test_root_help_groups_commands_under_their_panels():
    out = _run("--help")
    assert "Modules" in out and "Desktop app" in out and "Commands" in out
    assert out.index("Modules") < out.index("  add") < out.index("Desktop app") < out.index("  gui")


def test_a_bare_invocation_prints_the_same_page():
    assert _run() == _run("--help")


def test_leaf_help_lists_arguments_options_and_examples():
    out = _run("add", "--help")
    assert "Arguments" in out and "MODULE" in out
    assert "--dry-run" in out and "Show the plan only." in out
    assert "Examples" in out and "hub add sr" in out and "bring sushiruntime in" in out


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


def test_the_provider_is_called_as_a_plain_function_not_bound_to_the_group():
    seen = []

    def provider():
        console = Console(PlainRenderer(stream=io.StringIO()), Theme(), IconSet())
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
    group = typer.main.get_command(_app())
    ctx = click.Context(group, info_name="hub")
    first = group.get_command(ctx, "add")
    second = group.get_command(ctx, "add")
    assert first is second
    page = second.get_help(click.Context(second, info_name="add", parent=ctx))
    assert page.count("Usage: hub add") == 1


class _TerminalConsole:
    """Stands in for a sushicore Console whose Rich console is a terminal of a given colour."""

    theme = Theme()

    def __init__(
        self,
        color_system: str,
        no_color: bool = False,
        width: int = 80,
        dark_background: bool = False,
    ) -> None:
        """Build the Rich console as a terminal of ``width`` columns in ``color_system``."""
        self.dark_background = dark_background
        self.console = RichConsole(
            file=io.StringIO(),
            force_terminal=True,
            color_system=color_system,
            no_color=no_color,
            width=width,
        )


def _two_commands(app: typer.Typer) -> typer.Typer:
    """Add the two commands every help-screen app in this file carries."""

    @app.command("add")
    def add():
        """Bring a module in."""

    @app.command("doctor")
    def doctor():
        """Check tools."""

    return app


def _terminal_app(
    color_system: str,
    no_color: bool = False,
    width: int = 80,
    dark_background: bool = False,
) -> typer.Typer:
    """Return a two-command app whose help draws on a terminal of the given colour."""

    def provider() -> _TerminalConsole:
        return _TerminalConsole(color_system, no_color, width, dark_background)

    return _two_commands(typer.Typer(cls=help_group(provider), name="hub", help="Manage."))


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


@pytest.mark.parametrize("color_system", ["256", "truecolor"])
def test_the_root_page_shows_the_logo_on_a_terminal_with_256_colours_or_more(color_system):
    assert _shows_logo(CliRunner().invoke(_terminal_app(color_system), ["--help"]).output)


def test_a_dark_terminal_draws_the_lockup_with_its_glow():
    logo = Logo(glow=True)
    app = _terminal_app("truecolor", width=logo.width, dark_background=True)
    output = CliRunner().invoke(app, ["--help"]).output
    assert _block_rows(output) == _drawn_alone(logo, logo.width)


def test_a_light_terminal_draws_the_lockup_without_a_glow():
    logo = Logo(glow=False)
    app = _terminal_app("truecolor", width=logo.width)
    output = CliRunner().invoke(app, ["--help"]).output
    assert _block_rows(output) == _drawn_alone(logo, logo.width)


def test_a_console_too_narrow_for_the_wordmark_draws_the_mark_alone():
    mark = Logo(wordmark=False, glow=False)
    app = _terminal_app("truecolor", width=mark.width)
    output = CliRunner().invoke(app, ["--help"]).output
    assert _block_rows(output) == _drawn_alone(mark, mark.width)


def test_a_console_narrower_than_the_mark_draws_no_logo():
    app = _terminal_app("truecolor", width=Logo(wordmark=False, glow=False).width - 1)
    assert not _shows_logo(CliRunner().invoke(app, ["--help"]).output)


def test_a_leaf_page_does_not_show_the_logo_on_a_colour_terminal():
    output = CliRunner().invoke(_terminal_app("truecolor"), ["add", "--help"]).output
    assert not _shows_logo(output)


def test_the_root_page_hides_the_logo_on_a_standard_colour_terminal():
    assert not _shows_logo(CliRunner().invoke(_terminal_app("standard"), ["--help"]).output)


def test_the_root_page_hides_the_logo_when_colour_is_switched_off_on_a_terminal():
    app = _terminal_app("truecolor", no_color=True)
    assert not _shows_logo(CliRunner().invoke(app, ["--help"]).output)


def _guarded_app(provider, help_text: str = "Manage the stack.", **options) -> typer.Typer:
    """Return a two-command app whose help draws through ``provider``."""
    app = typer.Typer(cls=help_group(provider), name="hub", help=help_text, **options)
    return _two_commands(app)


def _warnings(caplog) -> list[logging.LogRecord]:
    """Return the warnings the help logger recorded."""
    return [
        record
        for record in caplog.records
        if record.name == K_LOGGER_NAME and record.levelno == logging.WARNING
    ]


def _invoke_and_warn(app: typer.Typer, caplog, *args: str) -> str:
    """Return the output of ``app`` with ``args``, asserting exit code 0 and one warning."""
    with caplog.at_level(logging.WARNING, logger=K_LOGGER_NAME):
        result = CliRunner().invoke(app, list(args))
    assert result.exit_code == 0, result.output
    assert len(_warnings(caplog)) == 1, [record.getMessage() for record in _warnings(caplog)]
    return result.output


def test_a_group_whose_provider_raises_falls_back_to_typers_help(caplog):
    def provider():
        raise RuntimeError("no workspace here")

    output = _invoke_and_warn(_guarded_app(provider), caplog, "--help")
    assert K_TYPER_PANEL in output
    assert "no workspace here" in _warnings(caplog)[0].getMessage()


def test_a_child_whose_provider_raises_falls_back_to_typers_help(caplog):
    def provider():
        raise ValueError("the config is unreadable")

    output = _invoke_and_warn(_guarded_app(provider), caplog, "add", "--help")
    assert K_TYPER_PANEL in output and "Bring a module in." in output


def test_a_help_group_used_without_a_provider_falls_back_to_typers_help(caplog):
    app = _two_commands(typer.Typer(cls=HelpGroup, name="hub", help="Manage the stack."))
    with caplog.at_level(logging.WARNING, logger=K_LOGGER_NAME):
        result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0, result.output
    assert K_TYPER_PANEL in result.output
    assert len(_warnings(caplog)) == 1


def test_a_stray_close_tag_in_rich_help_is_logged_and_handed_to_typers_help(caplog):
    console = Console(PlainRenderer(stream=io.StringIO()), Theme(), IconSet())
    app = _guarded_app(lambda: console, "Manage [/] the stack.", rich_markup_mode="rich")
    with caplog.at_level(logging.WARNING, logger=K_LOGGER_NAME):
        result = CliRunner().invoke(app, ["--help"])
    assert len(_warnings(caplog)) == 1
    assert "MarkupError" in _warnings(caplog)[0].getMessage()
    assert isinstance(result.exception, MarkupError)


def test_typer_alone_fails_on_the_same_stray_close_tag():
    app = _two_commands(typer.Typer(name="hub", help="Manage [/] the stack.",
                                    rich_markup_mode="rich"))
    assert isinstance(CliRunner().invoke(app, ["--help"]).exception, MarkupError)


def test_each_help_call_logs_one_warning_of_its_own(caplog):
    def provider():
        raise RuntimeError("no workspace here")

    app = _guarded_app(provider)
    with caplog.at_level(logging.WARNING, logger=K_LOGGER_NAME):
        CliRunner().invoke(app, ["--help"])
        CliRunner().invoke(app, ["add", "--help"])
    assert len(_warnings(caplog)) == 2
