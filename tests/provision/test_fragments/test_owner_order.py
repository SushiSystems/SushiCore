# test_owner_order.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Owners are reported in the order a build would need them."""

from __future__ import annotations

import pytest

from sushicore.provision.fragments import SHARED_OWNER, Dependency, owner_order
from sushicore.provision.fragments_memory import InMemoryDependencySource


pytestmark = pytest.mark.small


def dep(name: str, owner: str = SHARED_OWNER, *, provides: str = "",
        required: bool = True, linux_apt=(), windows_vcpkg=(),
        check_cmd=()) -> Dependency:
    """Build one :class:`Dependency` with the fields a test cares about."""
    return Dependency(
        name=name,
        description=f"{name} (test)",
        required=required,
        gpu_only=False,
        linux_apt=list(linux_apt),
        windows_vcpkg=list(windows_vcpkg),
        check_cmd=list(check_cmd),
        owner=owner,
        provides=provides,
    )


def test_shared_comes_first_then_dependency_order():
    """Check that shared comes first then dependency order."""
    src = InMemoryDependencySource(
        [dep("a", "sushiai"), dep("b", "sushiblas"), dep("r", "sushiruntime")],
        depends_on={"sushiai": ["sushiruntime", "sushiblas"], "sushiblas": ["sushiruntime"]})
    assert owner_order(src, ["sushiai", "shared", "sushiblas", "sushiruntime"]) == \
        ["shared", "sushiruntime", "sushiblas", "sushiai"]


def test_ties_keep_input_order():
    """Check that ties keep input order."""
    src = InMemoryDependencySource([], depends_on={})
    assert owner_order(src, ["sushidsp", "sushiengine"]) == ["sushidsp", "sushiengine"]


def test_a_cycle_is_refused():
    """Check that a cycle is refused."""
    src = InMemoryDependencySource([], depends_on={"x": ["y"], "y": ["x"]})
    with pytest.raises(ValueError):
        owner_order(src, ["x", "y"])
