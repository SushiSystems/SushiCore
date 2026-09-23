# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Owners are reported in the order a build would need them."""

from __future__ import annotations

import pytest

from sushicore.provision.fragments import SHARED_OWNER, Dependency, IDependencySource, owner_order


class MemorySource(IDependencySource):
    """Serves a fixed dependency list and a fixed module dependency map."""

    def __init__(self, deps: list[Dependency],
                 depends_on: dict[str, list[str]] | None = None) -> None:
        """Store the dependencies and the module-to-modules map to serve."""
        self._deps = list(deps)
        self._depends_on = dict(depends_on or {})

    def all(self) -> list[Dependency]:
        """Return the dependency list exactly as it was given."""
        return list(self._deps)

    def depends_on(self, owner: str) -> list[str]:
        """Return the modules *owner* directly builds on."""
        return list(self._depends_on.get(owner, []))


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
    src = MemorySource([dep("a", "sushiai"), dep("b", "sushiblas"), dep("r", "sushiruntime")],
                       depends_on={"sushiai": ["sushiruntime", "sushiblas"], "sushiblas": ["sushiruntime"]})
    assert owner_order(src, ["sushiai", "shared", "sushiblas", "sushiruntime"]) == \
        ["shared", "sushiruntime", "sushiblas", "sushiai"]


def test_ties_keep_input_order():
    src = MemorySource([], depends_on={})
    assert owner_order(src, ["sushidsp", "sushiengine"]) == ["sushidsp", "sushiengine"]


def test_a_cycle_is_refused():
    src = MemorySource([], depends_on={"x": ["y"], "y": ["x"]})
    with pytest.raises(ValueError):
        owner_order(src, ["x", "y"])
