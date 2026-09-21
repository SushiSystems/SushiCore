"""RichRenderer draws its table, panel and header through the components."""

import inspect
import os
import subprocess
import sys
from pathlib import Path

import pytest

from sushicore.renderer import RichRenderer
from sushicore.theme import Theme

K_FRAME = set("│┃┌┐└┘╭╮╰╯|+")
K_REPOSITORY = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _keep_the_real_console_untouched(monkeypatch):
    """Replace the Win32 switch with a no-op so no test here reaches the real console."""
    monkeypatch.setattr("sushicore.windows_console.enable_virtual_terminal", lambda: False)


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


def test_grouped_table_prints_a_heading_per_group_without_the_group_column(capsys):
    RichRenderer(Theme(), no_color=True).table(
        "Inventory",
        ["Owner", "Component", "Status"],
        [["shared", "python", "OK"], ["sushiruntime", "adaptivecpp", "MISSING"]],
        header_style="bold",
        group_by="Owner",
    )
    lines = _lines(capsys)
    assert [line for line in lines if line and line[0] not in " ─"] == [
        "Inventory",
        "shared",
        "sushiruntime",
    ]
    assert "Owner" not in "\n".join(lines)


def test_header_prints_a_blank_line_then_a_rule_holding_the_title(capsys):
    RichRenderer(Theme(), no_color=True).header("Setup", style="bold")
    lines = _lines(capsys)
    assert lines[0] == "" and "Setup" in lines[1] and "─" in lines[1]


def test_panel_prints_its_title_and_body_inside_a_border(capsys):
    RichRenderer(Theme(), no_color=True).panel("Failed", "cmake exited 1", border_style="red")
    lines = _lines(capsys)
    assert lines[0][0] in "╭┌" and "Failed" in lines[0]
    assert "cmake exited 1" in lines[1] and lines[2][0] in "╰└"


def _exit_code_when_loaded_after_import(module: str) -> subprocess.CompletedProcess:
    """Import sushicore in a fresh interpreter and exit 1 when ``module`` is loaded by it."""
    environment = {**os.environ, "PYTHONPATH": str(K_REPOSITORY)}
    return subprocess.run(
        [sys.executable, "-c", f"import sys, sushicore; sys.exit({module!r} in sys.modules)"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_sushicore_does_not_load_rich():
    """Import sushicore in a fresh interpreter and require that Rich stays unloaded."""
    result = _exit_code_when_loaded_after_import("rich")
    assert result.returncode == 0, result.stderr


def test_importing_sushicore_does_not_load_the_windows_console_module():
    """Import sushicore in a fresh interpreter and require that windows_console stays unloaded."""
    result = _exit_code_when_loaded_after_import("sushicore.windows_console")
    assert result.returncode == 0, result.stderr


def test_constructing_a_rich_renderer_switches_on_virtual_terminal_processing_once(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "sushicore.windows_console.enable_virtual_terminal", lambda: calls.append(1) or True,
    )
    RichRenderer(Theme(), no_color=True)
    assert calls == [1]


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
