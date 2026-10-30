# test_module_tests.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the defaults of what a module hands the shared test command."""

from pathlib import Path

import pytest

from sushicore.profile import ModuleProfile
from sushicore.testing.module_tests import ModuleTests

pytestmark = pytest.mark.small


def test_a_module_that_names_no_tree_check_has_no_fault_to_report():
    profile = ModuleProfile(name="sushitrack", program="st", env_prefix="ST", root_marker="m")
    module = ModuleTests(profile=profile, project_root=lambda: Path("."), console=lambda: None,
                         build_tree=lambda: Path("."), run_ctest=lambda tree, **keywords: 0,
                         run=lambda command, cwd: 0)
    assert module.check_tree(Path(".")) is None
    assert module.panel is None
