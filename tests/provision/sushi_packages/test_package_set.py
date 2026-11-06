# test_package_set.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the resolved packages a consumer reads."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.sushi_packages.package import Package
from sushicore.provision.sushi_packages.package_set import PackageSet, ResolvedPackage
from sushicore.provision.sushi_packages.package_store import PackageStore

from .package_fakes import install, make_key


@pytest.fixture
def values():
    """Return a built log package and a reused runtime package, held as values."""
    log = ResolvedPackage(Package("sushilog", "a" * 64, Path("log"), {}), None,
                          built=True, seconds=2.34)
    runtime = ResolvedPackage(Package("sushiruntime", "b" * 64, Path("rt"), {}), None,
                              built=False)
    return log, runtime


@pytest.fixture
def items(tmp_path):
    """Return a built log package and a reused runtime package, installed in a store."""
    store = PackageStore(tmp_path / "packages")
    log = ResolvedPackage(install(store, make_key("sushilog")), None, built=True, seconds=2.34)
    runtime = ResolvedPackage(install(store, make_key("sushiruntime")), None, built=False)
    return log, runtime


@pytest.mark.small
def test_a_line_says_reused_or_built_with_the_short_digest(values):
    """Check both line forms."""
    log, runtime = values
    assert (log.line(), runtime.line()) == (
        "sushilog: built aaaaaaaaaaaa in 2.3s", "sushiruntime: reused bbbbbbbbbbbb")


@pytest.mark.small
def test_lines_follow_the_dependency_order(values):
    """Check that the lines come in the order of the set."""
    assert PackageSet(values).lines() == [
        "sushilog: built aaaaaaaaaaaa in 2.3s", "sushiruntime: reused bbbbbbbbbbbb"]


@pytest.mark.medium
def test_definitions_use_the_spelling_of_each_package_and_the_closure(items):
    """Check one -D<Package>_DIR per package, with the library's own case."""
    names = [d.split("=")[0] for d in PackageSet(items).definitions()]
    assert names == ["-DSushiLog_DIR", "-DSushiRuntime_DIR"]


@pytest.mark.medium
def test_run_dirs_list_every_package_last_first(items):
    """Check that the bin folder of each package is listed, the last-resolved first."""
    dirs = PackageSet(items).run_dirs("windows")
    assert [d.split("sushi")[-1].split("\\")[0].split("/")[0] for d in dirs] == ["runtime", "log"]
