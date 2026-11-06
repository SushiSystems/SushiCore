# test_rich_components.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""RichRenderer draws its table, panel and header through the components."""

import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from sushicore.renderer import RichRenderer
from sushicore.theme import Theme


pytestmark = pytest.mark.medium

K_FRAME = set("│┃┌┐└┘╭╮╰╯|+")
K_REPOSITORY = Path(__file__).resolve().parent.parent


def _renderer() -> tuple[RichRenderer, io.StringIO]:
    """Return a renderer writing to a new in-memory stream, with the Win32 switch a no-op."""
    out = io.StringIO()
    return RichRenderer(Theme(), no_color=True, stream=out, enable_virtual_terminal=lambda: False), out


def _lines(out: io.StringIO) -> list[str]:
    """Return what the stream holds as lines, trailing spaces stripped."""
    return [line.rstrip() for line in out.getvalue().split("\n")]


def test_table_has_a_title_a_header_a_rule_and_no_frame():
    renderer, out = _renderer()
    renderer.table(
        "Modules", ["Module", "State"], [["sushiruntime", "cloned"]], header_style="bold",
    )
    lines = _lines(out)
    assert lines[0] == "Modules"
    assert lines[1].startswith("Module")
    assert set(lines[2]) == {"─"}
    assert not set("".join(lines)) & K_FRAME


def test_grouped_table_prints_a_heading_per_group_without_the_group_column():
    renderer, out = _renderer()
    renderer.table(
        "Inventory",
        ["Owner", "Component", "Status"],
        [["shared", "python", "OK"], ["sushiruntime", "adaptivecpp", "MISSING"]],
        header_style="bold",
        group_by="Owner",
    )
    lines = _lines(out)
    assert [line for line in lines if line and line[0] not in " ─"] == [
        "Inventory",
        "shared",
        "sushiruntime",
    ]
    assert "Owner" not in "\n".join(lines)


def test_header_prints_a_blank_line_then_a_rule_holding_the_title():
    renderer, out = _renderer()
    renderer.header("Setup", style="bold")
    lines = _lines(out)
    assert lines[0] == "" and "Setup" in lines[1] and "─" in lines[1]


def test_panel_prints_its_title_and_body_inside_a_border():
    renderer, out = _renderer()
    renderer.panel("Failed", "cmake exited 1", border_style="red")
    lines = _lines(out)
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


@pytest.mark.parametrize(
    "module", ["rich", "sushicore.windows_console"], ids=["rich", "windows_console"],
)
def test_importing_sushicore_does_not_load_the_module(module):
    """Import sushicore in a fresh interpreter and require that the module stays unloaded."""
    result = _exit_code_when_loaded_after_import(module)
    assert result.returncode == 0, result.stderr


def test_constructing_a_rich_renderer_switches_on_virtual_terminal_processing_once():
    calls = []
    RichRenderer(
        Theme(), no_color=True, stream=io.StringIO(),
        enable_virtual_terminal=lambda: calls.append(1) or True,
    )
    assert calls == [1]


@pytest.mark.parametrize(
    ("draw", "title", "tag"),
    [
        (lambda renderer, title: renderer.header(title, style="bold"), "[bold]Setup[/bold]", "[bold]"),
        (
            lambda renderer, title: renderer.panel(title, "body", border_style="red"),
            "[red]Failed[/red]",
            "[red]",
        ),
    ],
    ids=["header", "panel"],
)
def test_markup_in_a_title_is_parsed_not_printed(draw, title, tag):
    renderer, out = _renderer()
    draw(renderer, title)
    assert tag not in out.getvalue()
