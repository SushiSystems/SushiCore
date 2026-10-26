# test_closure_walk.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the walk over a consumer's chain."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.sushi_packages.closure_walk import ClosureWalk
from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.package_request import PackageRequest
from sushicore.provision.sushi_packages.source_locator import SushiSourceLocator

from .package_fakes import make_library

pytestmark = pytest.mark.medium


@pytest.fixture
def workspace(tmp_path):
    """Return a workspace holding the diamond: AI, BLAS, Runtime and Log."""
    make_library(tmp_path, "sushilog")
    make_library(tmp_path, "sushiruntime", ("sushilog",))
    make_library(tmp_path, "sushiblas", ("sushiruntime", "sushilog"))
    make_library(tmp_path, "sushiai", ("sushiblas", "sushiruntime"), cli="")
    return tmp_path


def _walk(workspace):
    """Return the names the walk lists for the consumer at *workspace*."""
    request = PackageRequest("sushiai", workspace / "sushiai", "c", "release")
    return ClosureWalk(SushiSourceLocator()).walk(request)


def test_the_diamond_lists_the_runtime_once_before_blas(workspace):
    """Check the dependency order and that no library appears twice."""
    names = [node.name for node in _walk(workspace)]
    assert names == ["sushilog", "sushiruntime", "sushiblas"]


def test_a_node_carries_its_cli_and_dependencies(workspace):
    """Check the fields of a node read from the fragment."""
    blas = _walk(workspace)[2]
    assert (blas.cli, blas.depends_on) == ("x", ("sushiruntime", "sushilog"))
    assert blas.checkout == (workspace / "sushiblas").resolve()


def test_a_cycle_raises_naming_the_trail(workspace):
    """Check that two libraries depending on each other are refused."""
    make_library(workspace, "sushilog", ("sushiruntime",))
    with pytest.raises(PackageError, match="sushiai -> sushiblas -> sushiruntime -> sushilog"):
        _walk(workspace)


def test_a_malformed_fragment_raises_a_package_error(workspace):
    """Check that a fragment the reader refuses reaches the caller as a package error."""
    (workspace / "sushilog" / "cli" / "sushistack.deps.toml").write_text(
        "[module]\ncli = 3\n", encoding="utf-8")
    with pytest.raises(PackageError, match="cli"):
        _walk(workspace)


def test_the_pin_of_the_consumer_decides_the_version(workspace, tmp_path):
    """Check that the consumer's pin is the version handed to the locator."""
    seen: list[tuple[str, str]] = []

    class _Locator:
        """Records the version asked for and answers the sibling."""

        def locate(self, root: Path, name: str, version: str, configured: str) -> Path:
            """Record the call and return the sibling checkout."""
            seen.append((name, version))
            return workspace / name

    text = ('[module]\ndepends_on = ["sushilog"]\n[sushisystems.sushilog]\n'
            'version = "v1.0.0"\ncommit = "' + "a" * 40 + '"\n')
    (workspace / "sushiai" / "cli" / "sushistack.deps.toml").write_text(text, encoding="utf-8")
    request = PackageRequest("sushiai", workspace / "sushiai", "c", "release")
    ClosureWalk(_Locator()).walk(request)
    assert seen == [("sushilog", "v1.0.0")]
