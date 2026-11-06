# test_default_resolver.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the assembly of the default package resolver and the public surface."""

from __future__ import annotations

from pathlib import Path

import pytest

import sushicore.provision.sushi_packages as sushi_packages
from sushicore.provision.sushi_packages import PackageError, default_resolver, effective_keep
from sushicore.provision.sushi_packages.lines_memory import RecordedLines
from sushicore.provision.sushi_packages.package_builder import MemoryRun
from sushicore.provision.sushi_packages.package_resolver import PackageResolver
from sushicore.provision.sushi_packages.source_state import MemoryInspector

pytestmark = pytest.mark.small


def test_the_public_surface_is_exactly_the_documented_names():
    """Check the names the package re-exports."""
    assert sorted(sushi_packages.__all__) == [
        "PackageConflictError", "PackageError", "PackageRequest", "PackageResolver",
        "PackageSet", "ResolvedPackage", "RunDirs", "configure_arguments", "default_resolver",
        "effective_keep", "search_path_variable"]


def test_default_resolver_starts_no_process():
    """Check that assembling the resolver runs no library CLI and lists no checkout."""
    run = MemoryRun(codes=())
    inspector = MemoryInspector({})
    resolver = default_resolver(3, RecordedLines(), RecordedLines(), env={}, run=run,
                                root=Path("packages"), inspector=inspector)
    assert (type(resolver), run.calls) == (PackageResolver, [])


def test_an_unset_keep_count_is_three():
    """Check that no configured count and no variable give three."""
    assert effective_keep(0, {}) == 3


def test_the_configured_keep_count_is_used_without_the_variable():
    """Check that a configured count stands when the variable is not set."""
    assert effective_keep(5, {}) == 5


def test_the_environment_overrides_the_configured_keep_count():
    """Check that the variable wins over the configured count."""
    assert effective_keep(5, {"SUSHISTACK_PACKAGE_KEEP": "2"}) == 2


@pytest.mark.parametrize("value", ["0", "-1", "many"])
def test_a_bad_keep_variable_is_refused(value):
    """Check that a value below 1 or not a number is refused."""
    with pytest.raises(PackageError, match="SUSHISTACK_PACKAGE_KEEP"):
        effective_keep(3, {"SUSHISTACK_PACKAGE_KEEP": value})
