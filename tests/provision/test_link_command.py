# test_link_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests linking a module into a workspace: the marker check, the one operation and the unlink."""

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.profile import ModuleProfile
from sushicore.provision import link_command
from sushicore.provision.module_provision import ModuleProvision
from sushicore.workspace import read_link, registered_modules


def _module(tmp_path, console, **overrides):
    """Return the module under test, its console *console*."""
    profile = ModuleProfile(name="sushidsp", program="sd", env_prefix="SD", root_marker="m")
    return ModuleProvision(profile=profile, project_root=lambda: tmp_path / "dsp",
                           load_config=lambda: None, console=lambda: console, **overrides)


def _errors(console):
    """Return the text of every error the recording console took."""
    return [args[0] for name, args in console.calls if name == "error"]


def _refuse(workspace, key, root):
    """Refuse to record a module, as a full disk does."""
    raise OSError("disk full")


def _workspace(path):
    (path / ".sushistack").mkdir(parents=True)
    return path


@pytest.mark.medium
def test_link_refuses_a_path_that_is_not_a_workspace_and_writes_nothing(tmp_path):
    console = RecordingConsole()
    plain = tmp_path / "plain"
    plain.mkdir()
    (tmp_path / "dsp" / "cli").mkdir(parents=True)
    outcome = link_command.run_link(_module(tmp_path, console), plain)
    assert (outcome.ok, outcome.code) == (False, 2)
    assert read_link(tmp_path / "dsp" / "cli") is None
    assert registered_modules(plain) == {}
    assert "is not a workspace" in _errors(console)[0]


@pytest.mark.medium
def test_link_puts_the_old_link_back_when_the_registry_write_fails(tmp_path):
    old, new = _workspace(tmp_path / "old"), _workspace(tmp_path / "new")
    (tmp_path / "dsp" / "cli").mkdir(parents=True)
    assert link_command.run_link(_module(tmp_path, RecordingConsole()), old).ok

    outcome = link_command.run_link(_module(tmp_path, RecordingConsole(), register=_refuse), new)
    assert (outcome.ok, outcome.code) == (False, 1)
    assert read_link(tmp_path / "dsp" / "cli") == old.resolve()


@pytest.mark.medium
def test_link_leaves_no_link_when_the_first_registry_write_fails(tmp_path):
    ws = _workspace(tmp_path / "ws")
    (tmp_path / "dsp" / "cli").mkdir(parents=True)

    console = RecordingConsole()
    assert link_command.run_link(_module(tmp_path, console, register=_refuse), ws).ok is False
    assert read_link(tmp_path / "dsp" / "cli") is None
    assert "disk full" in _errors(console)[0]


@pytest.mark.medium
def test_the_config_folder_comes_from_the_module(tmp_path):
    ws = _workspace(tmp_path / "ws")
    (tmp_path / "dsp" / "tooling").mkdir(parents=True)
    module = _module(tmp_path, RecordingConsole(), config_dir="tooling")
    assert link_command.run_link(module, ws).ok
    assert read_link(tmp_path / "dsp" / "tooling") == ws.resolve()
    assert link_command.run_unlink(module, ws).ok
    assert read_link(tmp_path / "dsp" / "tooling") is None
