# test_cli_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The machine flag picks the renderer before anything prints."""

import json
from pathlib import Path

import pytest

from sushicore import JsonRenderer, build_console
from sushicore.cli_console import LazyConsole


pytestmark = pytest.mark.small


def test_build_console_machine_uses_the_json_renderer():
    console = build_console([], machine=True)
    assert isinstance(console._renderer, JsonRenderer)


def test_lazy_console_reads_machine_at_first_build(monkeypatch, capsys):
    lazy = LazyConsole(lambda: Path("/nowhere"))
    lazy.machine = True
    lazy.attribute("info")("hello")
    assert json.loads(capsys.readouterr().out.strip()) == {"event": "line", "level": "info", "message": "hello"}


def test_lazy_console_exposes_the_new_names():
    lazy = LazyConsole(lambda: Path("/nowhere"))
    for name in ("table", "progress", "result", "prompt"):
        assert callable(lazy.attribute(name))


def test_lazy_console_is_machine_true_when_machine_flag_is_set():
    lazy = LazyConsole(lambda: Path("/nowhere"))
    lazy.machine = True
    assert lazy.attribute("is_machine")() is True


def test_lazy_console_is_machine_false_when_machine_flag_is_unset():
    lazy = LazyConsole(lambda: Path("/nowhere"))
    lazy.machine = False
    assert lazy.attribute("is_machine")() is False


def test_lazy_console_layers_extra_files_below_the_directory_files(tmp_path):
    workspace = tmp_path / "workspace.toml"
    lazy = LazyConsole(lambda: tmp_path / "cli", lambda: [workspace])
    assert lazy.sources() == [workspace, tmp_path / "cli" / "config.toml",
                              tmp_path / "cli" / "config.local.toml"]


def test_lazy_console_still_reads_extra_files_outside_a_checkout(tmp_path):
    def outside():
        raise SystemExit(1)

    workspace = tmp_path / "workspace.toml"
    assert LazyConsole(outside, lambda: [workspace]).sources() == [workspace]
    assert LazyConsole(outside).sources() == []


def test_lazy_console_takes_a_theme_from_a_file_it_was_given(tmp_path, capsys):
    workspace = tmp_path / "workspace.toml"
    workspace.write_text('[cli]\ntheme = "muted"\n', encoding="utf-8")
    lazy = LazyConsole(lambda: tmp_path / "cli", lambda: [workspace])
    assert lazy.get()._theme.cmd == "dim cyan"
