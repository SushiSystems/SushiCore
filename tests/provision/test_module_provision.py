# test_module_provision.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the defaults a module gets when its CLI hands the shared commands only what is required."""

from pathlib import Path

import pytest

from sushicore.profile import ModuleProfile
from sushicore.provision.module_provision import ModuleProvision


pytestmark = pytest.mark.small


def _module(**overrides):
    profile = ModuleProfile(name="sushidsp", program="sd", env_prefix="SD", root_marker="m")
    return ModuleProvision(profile=profile, project_root=lambda: Path("."), load_config=lambda: None,
                           console=lambda: None, **overrides)


def test_a_module_names_no_fragment_and_takes_the_cli_folder_by_default():
    module = _module()
    assert module.fragment is None
    assert module.config_dir == "cli"


def test_a_module_that_names_its_config_folder_keeps_it():
    assert _module(config_dir="tooling").config_dir == "tooling"


def test_a_module_checkout_is_never_found_by_default():
    assert _module().locate("anything") is None
    assert _module().is_binary() is False
