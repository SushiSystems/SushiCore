"""help_group draws every --help level as a HelpPage, or falls back to Typer's own."""

import io
import logging
import re

import pytest
import typer
import typer.main
from rich.console import Console as RichConsole
from rich.console import Group, RenderableType
from rich.errors import MarkupError
from rich.text import Text
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


def test_leaf_help_lists_arguments_options_and_examples():
    out = _run("add", "--help")
    assert "Arguments" in out and K_ARGUMENT_ROW.search(out)
    assert "--dry-run" in out and "Show the plan only." in out
    assert "Examples" in out and "hub add sr" in out and "bring sushiruntime in" in out


def test_leaf_help_shows_the_extras_typer_puts_on_a_parameter():
    out = _run("add", "--help")
    assert "The module.  [required]" in out
    assert "\\" not in out


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


def _terminal_page(*args: str, **shape) -> str:
    """Return what the terminal consoles of shape ``shape`` printed while ``args`` ran."""
    consoles: list[_TerminalConsole] = []

    def provider() -> _TerminalConsole:
        console = _TerminalConsole(**shape)
        consoles.append(console)
        return console

    app = _two_commands(typer.Typer(cls=help_group(provider), name="hub", help="Manage."))
    result = CliRunner().invoke(app, list(args))
    assert result.exit_code == 0, result.output
    return "".join(console.console.file.getvalue() for console in consoles)


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
    assert _shows_logo(_terminal_page("--help", color_system=color_system))


def test_the_page_reaches_a_truecolour_terminal_with_the_rolls_own_colour_codes():
    output = _terminal_page("--help", color_system="truecolor")
    assert K_AMBER_CODE in output and K_NORI_CODE in output


def test_the_root_page_leaves_one_blank_line_above_the_logo_and_two_below_it():
    output = _terminal_page("--help", color_system="truecolor", width=90, dark_background=True)
    lines = K_ANSI.sub("", output).split("\n")
    rows = [i for i, line in enumerate(lines) if _shows_logo(line)]
    assert lines[: rows[0]] == [""]
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
    return K_ANSI.sub("", result.output)


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
    assert K_TYPER_PANEL in K_ANSI.sub("", result.output)
    assert len(_warnings(caplog)) == 1


def test_a_stray_close_tag_in_rich_help_is_logged_and_handed_to_typers_help(caplog):
    console = _plain_console(io.StringIO())
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


class _Exploding:
    """Raises while Rich draws it, after the block before it has drawn."""

    def __rich_console__(self, console, options):
        """Raise instead of yielding segments."""
        raise RuntimeError("the second block cannot be drawn")


class _HalfDrawnPage:
    """Stands in for a page whose second block fails once the first has drawn."""

    def __init__(self, model, logo=None) -> None:
        """Take the arguments HelpPage takes and keep none of them."""

    def render(self, theme: Theme) -> RenderableType:
        """Return a block that draws and, after it, a block that raises."""
        return Group(Text(K_FIRST_BLOCK), _Exploding())


def test_a_block_that_fails_to_draw_leaves_no_part_of_the_page_on_the_console(monkeypatch, caplog):
    monkeypatch.setattr("sushicore.typer_help.HelpPage", _HalfDrawnPage)
    stream = io.StringIO()
    output = _invoke_and_warn(_app(_plain_console(stream)), caplog, "--help")
    assert stream.getvalue() == ""
    assert K_FIRST_BLOCK not in output and K_TYPER_PANEL in output
