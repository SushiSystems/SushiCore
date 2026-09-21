"""A help page prints the text of a Click or Typer command as written, and never raises on it."""

import click
import typer
import typer.main

from sushicore.help.from_click import build_model
from sushicore.help.page import HelpPage
from tests.ui.capture import capture

K_WIDTH = 100


def _page(command: click.Command, ctx: click.Context) -> str:
    """Return the help page of ``command`` as plain text."""
    return capture(HelpPage(build_model(command, ctx)), width=K_WIDTH)


def _typer_leaf(app: typer.Typer, name: str) -> tuple[click.Command, click.Context]:
    """Return the sub-command ``name`` of ``app`` and its context."""
    command = typer.main.get_command(app)
    parent = click.Context(command, info_name="tool")
    leaf = command.get_command(parent, name)
    return leaf, click.Context(leaf, info_name=name, parent=parent)


def _typer_app(**settings) -> typer.Typer:
    """Return a two-command Typer app whose docstring and options carry Rich markup."""
    app = typer.Typer(name="tool", **settings)

    @app.command(name="grow")
    def grow(
        module: str = typer.Argument(..., help="The module."),
        kind: str = typer.Option("a", "--kind", help="Kind."),
    ):
        """Paint [cyan]x[/cyan] here."""

    @app.command(name="rest")
    def rest():
        """Rest a while."""

    return app


def test_a_plain_click_option_shows_its_default_marker():
    @click.command(name="grow")
    @click.option("--kind", default="a", show_default=True, help="Kind.")
    def grow(kind):
        pass

    text = _page(grow, click.Context(grow, info_name="grow"))
    assert "Kind.  [default: a]" in text


def test_a_description_with_a_closing_tag_renders_and_prints_it():
    @click.command(name="grow", help="Close with [/] once.")
    def grow():
        pass

    text = _page(grow, click.Context(grow, info_name="grow"))
    assert "Close with [/] once." in text


def test_a_sub_command_short_help_with_a_bracket_prints_as_written():
    @click.group(name="hub")
    def hub():
        pass

    @hub.command(name="reset", help="Reset [hard] mode.")
    def reset():
        pass

    text = _page(hub, click.Context(hub, info_name="hub"))
    assert "Reset [hard] mode." in text


def test_a_typer_app_in_rich_mode_renders_its_markup_without_the_tags():
    leaf, ctx = _typer_leaf(_typer_app(rich_markup_mode="rich"), "grow")
    text = _page(leaf, ctx)
    assert "Paint x here." in text
    assert "[cyan]" not in text


def test_a_typer_app_in_rich_mode_shows_its_required_and_default_extras_without_a_backslash():
    leaf, ctx = _typer_leaf(_typer_app(rich_markup_mode="rich"), "grow")
    text = _page(leaf, ctx)
    assert "The module.  [required]" in text
    assert "Kind.  [default: a]" in text
    assert "\\" not in text


def test_a_typer_app_with_no_mode_set_shows_its_extras_without_a_backslash():
    leaf, ctx = _typer_leaf(_typer_app(), "grow")
    text = _page(leaf, ctx)
    assert "[required]" in text and "[default: a]" in text
    assert "\\" not in text
