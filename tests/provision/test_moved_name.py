# test_moved_name.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the names that moved out of a module and still answer from its old path."""

from __future__ import annotations

import importlib
import warnings

import pytest

from sushicore import link_pointer, layered_toml, workspace
from sushicore.provision import glob_search, gpu_vendor, intel_oneapi_repo, moved_name, probe, system
from sushicore.provision.packages import base, windows_path

pytestmark = pytest.mark.small

#: Each module that answers moved names, and the module each name moved to.
_MODULES = (system, probe, base, workspace)


def _moves() -> list[tuple[object, str, str]]:
    """Return every (old module, name, new module path) the four modules declare."""
    return [(module, name, destination)
            for module in _MODULES for name, destination in module.K_MOVED.items()]


@pytest.mark.parametrize("module, name, destination", _moves())
def test_a_moved_name_is_the_object_in_the_module_that_holds_it(module, name, destination):
    """Check that the old path hands out the current object, not a copy."""
    with pytest.warns(DeprecationWarning):
        found = getattr(module, name)
    assert found is getattr(importlib.import_module(destination), name)


@pytest.mark.parametrize("module, name, destination", _moves())
def test_a_moved_name_warns_with_its_new_home_and_points_at_the_caller(module, name, destination):
    """Check that the message names the new module and the warning points at this file."""
    with pytest.warns(DeprecationWarning, match=destination) as caught:
        getattr(module, name)
    assert caught[0].filename == __file__


def test_the_oneapi_repo_setup_is_found_through_the_system_module():
    """Check the one name the consumers import from its old module."""
    with pytest.warns(DeprecationWarning):
        assert system.ensure_intel_oneapi_repo is intel_oneapi_repo.ensure_intel_oneapi_repo


def test_the_moved_names_are_the_ones_each_module_held():
    """Check the tables list every name the module held and no more."""
    assert set(system.K_MOVED) == {"ensure_intel_oneapi_repo"}
    assert set(base.K_MOVED) == {"refresh_windows_path", "K_WINDOWS_PATH_SEPARATOR"}
    assert set(probe.K_MOVED) == {"K_RC_GLOBS", "first_existing", "is_integrated_adapter"}
    assert set(workspace.K_MOVED) == {
        "LINK_SECTION", "LinkEditError", "clear_link", "read_link", "write_link",
        "load_layered", "merge_platform_table"}


def test_the_destinations_are_the_modules_that_define_the_names():
    """Check each destination module is the one the name's definition sits in."""
    assert probe.K_MOVED["K_RC_GLOBS"] == glob_search.__name__
    assert probe.K_MOVED["is_integrated_adapter"] == gpu_vendor.__name__
    assert base.K_MOVED["refresh_windows_path"] == windows_path.__name__
    assert workspace.K_MOVED["read_link"] == link_pointer.__name__
    assert workspace.K_MOVED["load_layered"] == layered_toml.__name__


def test_a_name_the_module_never_had_is_still_an_attribute_error():
    """Check that the fallback does not answer every name."""
    with pytest.raises(AttributeError, match="no_such_name"):
        system.no_such_name


def test_a_name_the_module_defines_is_found_without_a_warning():
    """Check that the fallback is never reached for a name the module defines."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert system.is_root is not None


def test_the_resolver_rejects_a_name_absent_from_its_table():
    """Check the helper alone, with a table of its own."""
    with pytest.raises(AttributeError, match="gone"):
        moved_name.moved_attribute({"__name__": "demo"}, {}, "gone")
