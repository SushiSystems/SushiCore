# test_module_provision.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for what a module hands the shared commands."""

import pytest

from sushicore.profile import ModuleProfile
from sushicore.provision import module_plan
from sushicore.provision.module_provision import ModuleProvision

from .sushi_fakes import write_fragment


@pytest.mark.medium
def test_a_library_no_locator_and_no_sibling_provides_is_reported_missing(
        tmp_path, provision_home):
    """Check that a module that names no locator reports a pinned library nothing else provides."""
    root = tmp_path / "dsp"
    write_fragment(root, {"sushilog": "v1.0.0"})
    profile = ModuleProfile(name="sushidsp", program="sd", env_prefix="SD", root_marker="m")
    module = ModuleProvision(profile=profile, project_root=lambda: root, load_config=lambda: None,
                             console=lambda: None)

    assert module_plan.closure_for(module, root).missing == (("sushilog", "sushidsp"),)
