# test_setup_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the early exits of provisioning a module, which end before anything is installed."""

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.profile import ModuleProfile
from sushicore.provision import setup_command
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.git_client_memory import InMemoryGitClient
from sushicore.provision.machine_seams import MachineSeams
from sushicore.provision.module_provision import ModuleProvision


pytestmark = pytest.mark.medium


def _offline_git() -> InMemoryGitClient:
    """Return a git whose clones fail and whose every HEAD is a fixed commit."""
    return InMemoryGitClient(clones=False, default_head="0" * 40)


def test_an_unknown_toolchain_stops_setup_with_the_usage_code(tmp_path, provision_home):
    """Check that an unknown toolchain ends setup with the usage code and an error."""
    console = RecordingConsole()
    profile = ModuleProfile(name="sushidsp", program="sd", env_prefix="SD", root_marker="m")
    (tmp_path / "cli").mkdir()
    (tmp_path / "cli" / "sushistack.deps.toml").write_text('[widget]\ndescription = "w"\n', encoding="utf-8")
    module = ModuleProvision(profile=profile, project_root=lambda: tmp_path,
                             load_config=lambda: ProvisionSettings(platform="linux"),
                             console=lambda: console, git=_offline_git,
                             seams=MachineSeams(toolchains=lambda cfg, gpu: []))
    outcome = setup_command.run_setup(module, dry_run=True, yes=False, toolchains=["nonesuch"], gpu=False)
    assert (outcome.ok, outcome.code) == (False, 2)
    assert [name for name, _ in console.calls if name == "error"]
