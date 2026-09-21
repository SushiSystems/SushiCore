"""RichRenderer draws its table, panel and header through the components."""

import inspect
import os
import subprocess
import sys
from pathlib import Path

from sushicore.renderer import RichRenderer
from sushicore.theme import Theme

K_FRAME = set("│┃┌┐└┘╭╮╰╯|+")
K_REPOSITORY = Path(__file__).resolve().parent.parent


def _lines(capsys) -> list[str]:
    """Return the captured stdout as lines, trailing spaces stripped."""
    return [line.rstrip() for line in capsys.readouterr().out.split("\n")]


def test_table_has_a_title_a_header_a_rule_and_no_frame(capsys):
    RichRenderer(Theme(), no_color=True).table(
        "Modules", ["Module", "State"], [["sushiruntime", "cloned"]], header_style="bold",
    )
    lines = _lines(capsys)
    assert lines[0] == "Modules"
    assert lines[1].startswith("Module")
    assert set(lines[2]) == {"─"}
    assert not set("".join(lines)) & K_FRAME


def test_header_prints_a_blank_line_then_a_rule_holding_the_title(capsys):
    RichRenderer(Theme(), no_color=True).header("Setup", style="bold")
    lines = _lines(capsys)
    assert lines[0] == "" and "Setup" in lines[1] and "─" in lines[1]


def test_panel_prints_its_title_and_body_inside_a_border(capsys):
    RichRenderer(Theme(), no_color=True).panel("Failed", "cmake exited 1", border_style="red")
    lines = _lines(capsys)
    assert lines[0][0] in "╭┌" and "Failed" in lines[0]
    assert "cmake exited 1" in lines[1] and lines[2][0] in "╰└"


def test_importing_sushicore_does_not_load_rich():
    """Import sushicore in a fresh interpreter and require that Rich stays unloaded."""
    environment = {**os.environ, "PYTHONPATH": str(K_REPOSITORY)}
    result = subprocess.run(
        [sys.executable, "-c", "import sys, sushicore; sys.exit('rich' in sys.modules)"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_header_title_keeps_parsing_markup(capsys):
    RichRenderer(Theme(), no_color=True).header("[bold]Setup[/bold]", style="bold")
    out = capsys.readouterr().out
    assert "Setup" in out and "[bold]" not in out


def test_panel_title_keeps_parsing_markup(capsys):
    RichRenderer(Theme(), no_color=True).panel("[red]Failed[/red]", "body", border_style="red")
    out = capsys.readouterr().out
    assert "Failed" in out and "[red]" not in out


def test_the_delegating_methods_state_what_they_print_in_one_sentence():
    for method in (RichRenderer.header, RichRenderer.panel, RichRenderer.table):
        summary = inspect.getdoc(method)
        assert summary is not None and ";" not in summary and summary.count(".") == 1, summary
