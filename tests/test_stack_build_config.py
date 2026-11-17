# test_stack_build_config.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a module's build environment reads only the fields the stack build config names."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.build_env import StackBuildEnv
from sushicore.profile import ModuleProfile


class _Fields:
    """A config holding the stack build fields and one sibling directory."""

    platform = "linux"
    vs_vcvars = ""
    is_windows = False
    vcpkg_triplet = "x64-linux"
    core_dir = "/ws/core"

    def expand(self, value: str) -> str:
        """Return the value unchanged."""
        return value

    def bundled_llvm_root(self, root: Path) -> Path | None:
        """Report that no bundle is installed."""
        return None

    def resolved_vcpkg(self, root: Path) -> str:
        """Report that no vcpkg is set."""
        return ""


@pytest.mark.small
def test_a_config_with_only_those_fields_leaves_the_environment_untouched(tmp_path):
    """Check that without a bundle and off Windows the injection adds nothing."""
    env = StackBuildEnv(profile=ModuleProfile("SushiTest", "st", "ST", siblings=("core",)),
                        console=None, find_root=lambda: tmp_path)
    environment = {"PATH": "/usr/bin"}
    env.inject_toolchain(_Fields(), environment)
    assert environment == {"PATH": "/usr/bin"}


@pytest.mark.small
def test_the_cache_key_reads_the_sibling_directory_by_the_profiles_name():
    """Check that a sibling the profile names, and the config holds, is part of the key."""
    env = StackBuildEnv(profile=ModuleProfile("SushiTest", "st", "ST", siblings=("core",)),
                        console=None, find_root=lambda: Path("."))
    moved = _Fields()
    moved.core_dir = "/elsewhere"
    assert env.cache_key(moved) != env.cache_key(_Fields())
