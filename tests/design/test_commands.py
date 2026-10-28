# test_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the `design` group a CLI registers."""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from sushicore.design import OwnedModuleError, register_design_commands

pytestmark = pytest.mark.medium


def _invoke(root: Path, *arguments: str) -> tuple[int, list[str]]:
    """Runs one command of an application named `sx` and returns its code and its lines."""
    reported: list[str] = []
    app = typer.Typer(name="sx", no_args_is_help=True, add_completion=False)

    @app.command("build")
    def build() -> None:
        """Build."""

    register_design_commands(app, program="sx", panel="Project", project_root=lambda: root, report=reported.append)
    result = CliRunner().invoke(app, ["design", *arguments])
    if result.exception and not isinstance(result.exception, SystemExit):
        raise result.exception
    return result.exit_code, reported


def test_new_then_list_and_owner(store):
    """An agent opens a topic and reads who owns a path."""
    root = store.root
    code, lines = _invoke(root, "new", "ATMOSPHERE", "--modules", "modules/atmosphere", "--about", "The air.")
    assert (code, lines) == (0, ["docs/design/ATMOSPHERE/README.md"])
    _, lines = _invoke(root, "list", "--json")
    assert json.loads(lines[0])[0]["modules"] == ["modules/atmosphere"]
    assert _invoke(root, "owner", "modules/atmosphere/sky") == (0, ["ATMOSPHERE"])
    assert _invoke(root, "owner", "modules/clouds") == (0, ["none"])


def test_new_refuses_an_owned_module(store):
    """The second topic on a module is refused and the owner is named."""
    root = store.root
    _invoke(root, "new", "ATMOSPHERE", "--modules", "modules/atmosphere", "--about", "The air.")
    with pytest.raises(OwnedModuleError):
        _invoke(root, "new", "SKY", "--modules", "modules/atmosphere/sky", "--about", "The sky.")


def test_phase_commands_and_check(store):
    """Phases are added and moved; check is clean, then fails on a hand-made overlap."""
    root = store.root
    _invoke(root, "new", "ATMOSPHERE", "--modules", "modules/atmosphere", "--about", "The air.")
    assert _invoke(root, "phase", "ATMOSPHERE", "A1", "Scatter light") == (0, ["ATMOSPHERE#A1 planned"])
    shipped = f"Shipped — {datetime.date.today().isoformat()}"
    assert _invoke(root, "phase-state", "ATMOSPHERE", "A1", "built") == (0, [shipped])
    assert _invoke(root, "check") == (0, ["clean"])
    _invoke(root, "new", "CLOUDS", "--modules", "modules/clouds", "--about", "Clouds.")
    path = store.topic("CLOUDS").path
    path.write_text(path.read_text(encoding="utf-8").replace("`modules/clouds`", "`modules/clouds`, `modules/atmosphere`"), encoding="utf-8")
    code, lines = _invoke(root, "check")
    assert code == 1 and "owned by ATMOSPHERE" in lines[0]
    _, lines = _invoke(root, "overlap")
    assert lines[0] == "shared modules/atmosphere: ATMOSPHERE, CLOUDS"
    code, lines = _invoke(root, "merge", "ATMOSPHERE", "CLOUDS")
    assert lines[0] == "docs/design/ATMOSPHERE/CLOUDS.md"
    assert _invoke(root, "check") == (0, ["clean"])
