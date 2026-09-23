# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""What the detect step's inventory rows say, and in what order."""

from __future__ import annotations

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments import SHARED_OWNER, Dependency, IDependencySource
from sushicore.provision.pipeline import InstallContext
from sushicore.provision.steps import DetectStep


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


_TOOLCHAIN_ROWS = [
    ("intel-llvm", False, ""), ("adaptivecpp", False, ""),
    ("oneapi", False, ""), ("cuda", False, ""),
]


def _step(src):
    """Build a DetectStep with fixed toolchain and GPU-vendor probes."""
    return DetectStep(src, managers=[],
                      toolchain_status=lambda cfg, gpu: _TOOLCHAIN_ROWS,
                      gpu_vendor=lambda: "none")


def _ctx():
    """Build a Linux install context with no probed tool paths."""
    return InstallContext(cfg=ProvisionSettings(platform="linux"))


def test_undeclared_toolchains_are_not_needed():
    src = MemorySource([dep("cmake")])
    rows = _step(src).inventory_rows(_ctx(), src.all())
    status = {name: s for name, s, _o, _d in rows}
    assert status["intel-llvm"] == "NOT NEEDED" and status["cuda"] == "NOT NEEDED"


def test_declared_toolchains_are_missing_when_absent():
    src = MemorySource([dep("intel-llvm", "sushiruntime")])
    rows = _step(src).inventory_rows(_ctx(), src.all())
    assert dict((n, s) for n, s, _o, _d in rows)["intel-llvm"] == "MISSING"


def test_rows_are_grouped_by_owner_in_dependency_order():
    src = MemorySource([dep("a", "sushiai"), dep("r", "sushiruntime"), dep("cmake")],
                       depends_on={"sushiai": ["sushiruntime"]})
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"))
    owners = [o for _n, _s, o, _d in _step(src).inventory_rows(ctx, src.all())]
    first_index = {o: owners.index(o) for o in dict.fromkeys(owners)}
    assert first_index["shared"] < first_index["sushiruntime"] < first_index["sushiai"]
