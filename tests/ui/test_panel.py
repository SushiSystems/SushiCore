"""A panel is a bordered body under a title."""

from rich.markup import escape

from sushicore.ui.panel import Panel
from tests.ui.capture import capture


def test_panel_puts_the_title_on_the_top_border_and_the_body_inside():
    lines = capture(Panel("Build failed", "cmake exited 1"), width=30).rstrip("\n").split("\n")
    assert lines[0].startswith("╭") and "Build failed" in lines[0]
    assert "cmake exited 1" in lines[1]
    assert lines[-1].startswith("╰")


def test_panel_body_keeps_rich_markup():
    text = capture(Panel("t", "[bold]done[/bold]"), width=30)
    assert "done" in text and "[bold]" not in text


def test_a_marked_up_title_prints_without_its_tags():
    top = capture(Panel("[red]Failed[/red]", "body"), width=30).split("\n")[0]
    assert "Failed" in top and "[red]" not in top


def test_an_escaped_bracket_in_a_title_prints_literally():
    top = capture(Panel(escape("Build [debug]"), "body"), width=30).split("\n")[0]
    assert "Build [debug]" in top
