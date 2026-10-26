# test_package_set.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the resolved packages a consumer reads."""

from __future__ import annotations

import pytest

from sushicore.provision.sushi_packages.package_set import PackageSet, ResolvedPackage
from sushicore.provision.sushi_packages.package_store import PackageStore

from .package_fakes import install, make_key

pytestmark = pytest.mark.medium


@pytest.fixture
def items(tmp_path):
    """Return a built log package and a reused runtime package."""
    store = PackageStore(tmp_path / "packages")
    log = ResolvedPackage(install(store, make_key("sushilog")), None, built=True, seconds=2.34)
    runtime = ResolvedPackage(install(store, make_key("sushiruntime")), None, built=False)
    return log, runtime


def test_a_line_says_reused_or_built_with_the_short_digest(items):
    """Check both line forms."""
    log, runtime = items
    assert log.line() == f"sushilog: built {log.package.digest[:12]} in 2.3s"
    assert runtime.line() == f"sushiruntime: reused {runtime.package.digest[:12]}"


def test_lines_follow_the_dependency_order(items):
    """Check that the lines come in the order of the set."""
    assert PackageSet(items).lines()[0].startswith("sushilog")


def test_definitions_use_the_spelling_of_each_package_and_the_closure(items):
    """Check one -D<Package>_DIR per package, with the library's own case."""
    names = [d.split("=")[0] for d in PackageSet(items).definitions()]
    assert names == ["-DSushiLog_DIR", "-DSushiRuntime_DIR"]


def test_run_dirs_list_every_package_last_first(items):
    """Check that the bin folder of each package is listed, the last-resolved first."""
    dirs = PackageSet(items).run_dirs("windows")
    assert [d.split("sushi")[-1].split("\\")[0].split("/")[0] for d in dirs] == ["runtime", "log"]


def test_get_and_names(items):
    """Check the lookup by name and the list of names."""
    result = PackageSet(items)
    assert result.names() == ["sushilog", "sushiruntime"]
    assert result.get("sushilog") is items[0] and result.get("x") is None
