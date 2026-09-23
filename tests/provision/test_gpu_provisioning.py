# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""``provision_gpu_adapters`` reads one commit and drives one build per located backend."""

from __future__ import annotations

from types import SimpleNamespace

from sushicore.provision.gpu.backend import GpuBackendSpec, ToolkitInstall
from sushicore.provision.gpu.provisioning import provision_gpu_adapters
from sushicore.provision.gpu.registry import Registry

_COMMIT = "d5f649b706f63b5c74e1929bc95db8de91085560"


class _FakeLocator:
    """Reports a fixed install, or none, for one backend."""

    def __init__(self, install: ToolkitInstall | None) -> None:
        """Store the install this locator always reports."""
        self._install = install

    def locate(self, cfg) -> ToolkitInstall | None:
        """Return the stored install."""
        return self._install

    def provision(self, cfg, dry_run: bool) -> bool:
        """Never called by provisioning; present only to satisfy the protocol."""
        return True


def _spec(vendor: str, install: ToolkitInstall | None) -> GpuBackendSpec:
    """Build one GpuBackendSpec whose locator reports *install*."""
    return GpuBackendSpec(
        vendor=vendor,
        probe_vendor=f"{vendor}vendor",
        locator=_FakeLocator(install),
        adapter_option=f"UR_BUILD_ADAPTER_{vendor.upper()}",
        adapter_definitions=lambda install: {},
        adapter_target=f"ur_adapter_{vendor}",
        adapter_binaries=(f"ur_adapter_{vendor}",),
    )


class _FakeBuilder:
    """Records every spec it was asked to build and reports a fixed outcome per vendor."""

    def __init__(self, outcomes: dict[str, bool]) -> None:
        """Store which vendor's build should succeed or fail."""
        self._outcomes = outcomes
        self.built: list[str] = []

    def build(self, spec, install, toolchain_root, commit, dry_run) -> bool:
        """Record the call and return the outcome configured for this vendor."""
        self.built.append(spec.vendor)
        return self._outcomes.get(spec.vendor, True)


def _cfg() -> SimpleNamespace:
    """A Linux configuration stand-in; the commit reader is faked, so no real clang++ runs."""
    return SimpleNamespace(platform="linux", is_windows=False)


def test_a_missing_commit_builds_nothing(tmp_path, recording_console):
    registry = Registry((_spec("cuda", ToolkitInstall(root=tmp_path, version=None)),))
    builder = _FakeBuilder({})

    provision_gpu_adapters(
        _cfg(), registry, tmp_path, builder, dry_run=False,
        commit_reader=lambda path: None,
    )

    assert builder.built == []


def test_a_backend_with_no_located_toolkit_is_skipped(tmp_path, recording_console):
    registry = Registry((
        _spec("cuda", None),
        _spec("rocm", ToolkitInstall(root=tmp_path, version=None)),
    ))
    builder = _FakeBuilder({})

    provision_gpu_adapters(
        _cfg(), registry, tmp_path, builder, dry_run=False,
        commit_reader=lambda path: _COMMIT,
    )

    assert builder.built == ["rocm"]


def test_one_built_and_one_failed_are_both_called_and_neither_raises(
        tmp_path, recording_console):
    registry = Registry((
        _spec("cuda", ToolkitInstall(root=tmp_path, version=None)),
        _spec("rocm", ToolkitInstall(root=tmp_path, version=None)),
    ))
    builder = _FakeBuilder({"cuda": True, "rocm": False})

    provision_gpu_adapters(
        _cfg(), registry, tmp_path, builder, dry_run=False,
        commit_reader=lambda path: _COMMIT,
    )

    assert builder.built == ["cuda", "rocm"]
    assert recording_console.calls == []


def test_a_locator_that_raises_is_swallowed_and_warned(tmp_path, recording_console):
    class _BrokenLocator:
        def locate(self, cfg):
            raise OSError("disk unreadable")

    spec = GpuBackendSpec(
        vendor="cuda", probe_vendor="nvidia", locator=_BrokenLocator(),
        adapter_option="UR_BUILD_ADAPTER_CUDA", adapter_definitions=lambda install: {},
        adapter_target="ur_adapter_cuda", adapter_binaries=("ur_adapter_cuda",),
    )
    registry = Registry((spec,))
    builder = _FakeBuilder({})

    provision_gpu_adapters(
        _cfg(), registry, tmp_path, builder, dry_run=False,
        commit_reader=lambda path: _COMMIT,
    )

    assert builder.built == []
    warnings = [args[0] for name, args in recording_console.calls if name == "warn"]
    assert any("GPU adapter provisioning failed" in w and "OSError" in w
               and "disk unreadable" in w for w in warnings)


def test_a_missing_commit_warns(tmp_path, recording_console):
    registry = Registry((_spec("cuda", ToolkitInstall(root=tmp_path, version=None)),))
    builder = _FakeBuilder({})

    provision_gpu_adapters(
        _cfg(), registry, tmp_path, builder, dry_run=False,
        commit_reader=lambda path: None,
    )

    assert builder.built == []
    warnings = [args[0] for name, args in recording_console.calls if name == "warn"]
    assert any("Could not read the intel/llvm commit" in w for w in warnings)


def test_a_missing_commit_in_dry_run_prints_the_dry_run_line_instead_of_a_warning(
        tmp_path, recording_console):
    registry = Registry((_spec("cuda", ToolkitInstall(root=tmp_path, version=None)),))
    builder = _FakeBuilder({})

    provision_gpu_adapters(
        _cfg(), registry, tmp_path, builder, dry_run=True,
        commit_reader=lambda path: None,
    )

    infos = [args[0] for name, args in recording_console.calls if name == "info"]
    warnings = [args[0] for name, args in recording_console.calls if name == "warn"]
    assert any("would read the compiler commit" in i for i in infos)
    assert not any("Could not read" in w for w in warnings)
