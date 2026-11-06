# test_cli_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The machine flag picks the renderer before anything prints."""

import json
from pathlib import Path

import pytest

from sushicore.cli_console import LazyConsole

K_CHECKOUT = Path("checkout")


@pytest.mark.medium
def test_lazy_console_reads_machine_at_first_build(monkeypatch, capsys):
    lazy = LazyConsole(lambda: Path("/nowhere"))
    lazy.machine = True
    lazy.attribute("info")("hello")
    assert json.loads(capsys.readouterr().out.strip()) == {"event": "line", "level": "info", "message": "hello"}


@pytest.mark.medium
@pytest.mark.parametrize("name", ["table", "progress", "result", "prompt"])
def test_lazy_console_exposes_the_new_names(name):
    lazy = LazyConsole(lambda: Path("/nowhere"))
    assert callable(lazy.attribute(name))


@pytest.mark.medium
@pytest.mark.parametrize("machine", [True, False])
def test_lazy_console_is_machine_follows_the_machine_flag(machine):
    lazy = LazyConsole(lambda: Path("/nowhere"))
    lazy.machine = machine
    assert lazy.attribute("is_machine")() is machine


@pytest.mark.small
def test_lazy_console_layers_extra_files_below_the_directory_files():
    workspace = K_CHECKOUT / "workspace.toml"
    lazy = LazyConsole(lambda: K_CHECKOUT / "cli", lambda: [workspace])
    assert lazy.sources() == [workspace, K_CHECKOUT / "cli" / "config.toml",
                              K_CHECKOUT / "cli" / "config.local.toml"]


@pytest.mark.small
def test_lazy_console_still_reads_extra_files_outside_a_checkout():
    def outside():
        raise SystemExit(1)

    workspace = K_CHECKOUT / "workspace.toml"
    assert LazyConsole(outside, lambda: [workspace]).sources() == [workspace]
    assert LazyConsole(outside).sources() == []


@pytest.mark.medium
def test_lazy_console_takes_a_theme_from_a_file_it_was_given(tmp_path):
    workspace = tmp_path / "workspace.toml"
    workspace.write_text('[cli]\ntheme = "muted"\n', encoding="utf-8")
    lazy = LazyConsole(lambda: tmp_path / "cli", lambda: [workspace])
    assert lazy.get().theme.cmd == "dim cyan"


@pytest.mark.small
def test_lazy_console_is_not_built_until_it_is_first_used():
    assert LazyConsole(lambda: K_CHECKOUT).built is False
