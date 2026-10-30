# test_setup_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the early exits of provisioning a module, which end before anything is installed."""

import pytest

from sushicore.profile import ModuleProfile
from sushicore.provision import setup_command
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.git_client import IGitClient
from sushicore.provision.module_provision import ModuleProvision


pytestmark = pytest.mark.medium


class _Console:
    def __init__(self):
        self.errors = []

    def error(self, text):
        self.errors.append(text)

    def info(self, text):
        pass

    def warn(self, text):
        pass

    def success(self, text):
        pass


class _OfflineGit(IGitClient):
    def clone_tag(self, url, tag, destination, dry_run):
        return False

    def head(self, checkout):
        return "0" * 40


def test_an_unknown_toolchain_stops_setup_with_the_usage_code(tmp_path, provision_home):
    console = _Console()
    profile = ModuleProfile(name="sushidsp", program="sd", env_prefix="SD", root_marker="m")
    (tmp_path / "cli").mkdir()
    (tmp_path / "cli" / "sushistack.deps.toml").write_text('[widget]\ndescription = "w"\n', encoding="utf-8")
    module = ModuleProvision(profile=profile, project_root=lambda: tmp_path,
                             load_config=lambda: ProvisionSettings(platform="linux"),
                             console=lambda: console, git=_OfflineGit)
    outcome = setup_command.run_setup(module, dry_run=True, yes=False, toolchains=["nonesuch"], gpu=False)
    assert (outcome.ok, outcome.code) == (False, 2)
    assert console.errors
