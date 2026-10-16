# test_pin_chain.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the walk that finds a library pinned at two versions in one chain."""

from __future__ import annotations

import pytest

from sushicore.deps_fragment import read
from sushicore.provision.pin_chain import PinConflict, conflicts

from .sushi_fakes import write_fragment

pytestmark = pytest.mark.medium


def _chain(tmp_path, log_version_of_blas):
    """Lay out sushiai -> sushiblas -> sushiruntime -> sushilog, sushiai also pinning sushilog.

    sushiai pins sushilog at v1.0.0; sushiruntime pins it at *log_version_of_blas*.
    """
    ws = tmp_path / "ws"
    write_fragment(ws / "sushiai", {"sushiblas": "v2.0.0", "sushilog": "v1.0.0"})
    write_fragment(ws / "sushiblas", {"sushiruntime": "v3.0.0"})
    write_fragment(ws / "sushiruntime", {"sushilog": log_version_of_blas})
    (ws / "sushilog").mkdir()
    root = ws / "sushiai"
    return root, read(root / "cli" / "sushistack.deps.toml").pins


def test_a_chain_pinning_one_version_has_no_conflict(tmp_path, provision_home):
    """Check that three levels pinning sushilog at one version agree."""
    root, pins = _chain(tmp_path, "v1.0.0")
    assert conflicts("sushiai", root, pins) == []


def test_a_chain_pinning_two_versions_names_both_repositories(tmp_path, provision_home):
    """Check that a third-level pin at another version is a conflict naming both pinners."""
    root, pins = _chain(tmp_path, "v1.1.0")

    found = conflicts("sushiai", root, pins)

    assert found == [PinConflict("sushilog", "sushiai", "v1.0.0", "sushiruntime", "v1.1.0")]
    message = found[0].message()
    for part in ("sushilog", "sushiai", "v1.0.0", "sushiruntime", "v1.1.0"):
        assert part in message


def test_a_library_with_no_checkout_ends_its_branch(tmp_path, provision_home):
    """Check that an unresolved library is not walked and raises nothing."""
    root = tmp_path / "ws" / "sushiai"
    write_fragment(root, {"sushiblas": "v2.0.0"})
    pins = read(root / "cli" / "sushistack.deps.toml").pins
    assert conflicts("sushiai", root, pins) == []
