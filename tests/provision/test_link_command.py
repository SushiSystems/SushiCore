# test_link_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests linking a module into a workspace: the marker check, the one operation and the unlink."""

import pytest

from sushicore.profile import ModuleProfile
from sushicore.provision import link_command
from sushicore.provision.module_provision import ModuleProvision
from sushicore.workspace import read_link, registered_modules


pytestmark = pytest.mark.small


class _Console:
    def __init__(self):
        self.errors = []

    def error(self, text):
        self.errors.append(text)

    def success(self, text):
        pass

    def info(self, text):
        pass


def _module(tmp_path, console, **overrides):
    profile = ModuleProfile(name="sushidsp", program="sd", env_prefix="SD", root_marker="m")
    return ModuleProvision(profile=profile, project_root=lambda: tmp_path / "dsp",
                           load_config=lambda: None, console=lambda: console, **overrides)


def _workspace(path):
    (path / ".sushistack").mkdir(parents=True)
    return path


def test_link_refuses_a_path_that_is_not_a_workspace_and_writes_nothing(tmp_path):
    console = _Console()
    plain = tmp_path / "plain"
    plain.mkdir()
    (tmp_path / "dsp" / "cli").mkdir(parents=True)
    outcome = link_command.run_link(_module(tmp_path, console), plain)
    assert (outcome.ok, outcome.code) == (False, 2)
    assert read_link(tmp_path / "dsp" / "cli") is None
    assert registered_modules(plain) == {}
    assert "is not a workspace" in console.errors[0]


def test_link_puts_the_old_link_back_when_the_registry_write_fails(tmp_path, monkeypatch):
    old, new = _workspace(tmp_path / "old"), _workspace(tmp_path / "new")
    (tmp_path / "dsp" / "cli").mkdir(parents=True)
    module = _module(tmp_path, _Console())
    assert link_command.run_link(module, old).ok

    def refuse(*arguments, **keywords):
        raise OSError("disk full")

    monkeypatch.setattr(link_command, "write_module", refuse)
    outcome = link_command.run_link(module, new)
    assert (outcome.ok, outcome.code) == (False, 1)
    assert read_link(tmp_path / "dsp" / "cli") == old.resolve()


def test_link_leaves_no_link_when_the_first_registry_write_fails(tmp_path, monkeypatch):
    ws = _workspace(tmp_path / "ws")
    (tmp_path / "dsp" / "cli").mkdir(parents=True)

    def refuse(*arguments, **keywords):
        raise OSError("disk full")

    monkeypatch.setattr(link_command, "write_module", refuse)
    console = _Console()
    assert link_command.run_link(_module(tmp_path, console), ws).ok is False
    assert read_link(tmp_path / "dsp" / "cli") is None
    assert "disk full" in console.errors[0]


def test_the_config_folder_comes_from_the_module(tmp_path):
    ws = _workspace(tmp_path / "ws")
    (tmp_path / "dsp" / "tooling").mkdir(parents=True)
    module = _module(tmp_path, _Console(), config_dir="tooling")
    assert link_command.run_link(module, ws).ok
    assert read_link(tmp_path / "dsp" / "tooling") == ws.resolve()
    assert link_command.run_unlink(module, ws).ok
    assert read_link(tmp_path / "dsp" / "tooling") is None
