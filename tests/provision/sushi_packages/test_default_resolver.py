# test_default_resolver.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the assembly of the default package resolver and the public surface."""

from __future__ import annotations

import subprocess

import pytest

import sushicore.provision.sushi_packages as sushi_packages
from sushicore.provision.sushi_packages import PackageError, default_resolver, effective_keep

pytestmark = pytest.mark.medium


def test_the_public_surface_is_exactly_the_documented_names():
    """Check the names the package re-exports."""
    assert sorted(sushi_packages.__all__) == [
        "PackageConflictError", "PackageError", "PackageRequest", "PackageResolver",
        "PackageSet", "ResolvedPackage", "default_resolver", "effective_keep"]


def test_default_resolver_starts_no_process(provision_home, monkeypatch):
    """Check that assembling the resolver runs neither git nor a CLI."""
    def refuse(*_args, **_kwargs):
        """Fail the test when a process starts."""
        raise AssertionError("a process started")

    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(subprocess, "Popen", refuse)
    default_resolver(3, lambda _line: None, lambda _text: None, env={})


def test_the_keep_count_is_three_by_default_and_the_environment_overrides_it():
    """Check the default, the configured value and the variable."""
    assert effective_keep(0, {}) == 3
    assert effective_keep(5, {}) == 5
    assert effective_keep(5, {"SUSHISTACK_PACKAGE_KEEP": "2"}) == 2


@pytest.mark.parametrize("value", ["0", "-1", "many"])
def test_a_bad_keep_variable_is_refused(value):
    """Check that a value below 1 or not a number is refused."""
    with pytest.raises(PackageError, match="SUSHISTACK_PACKAGE_KEEP"):
        effective_keep(3, {"SUSHISTACK_PACKAGE_KEEP": value})
