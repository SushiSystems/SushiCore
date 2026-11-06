# test_provisioning.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""``provision_gpu_adapters`` reads one commit and drives one build per located backend."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from sushicore.provision.gpu.adapter_builder_memory import InMemoryAdapterBuilder
from sushicore.provision.gpu.backend import GpuBackendSpec, ToolkitInstall
from sushicore.provision.gpu.backend_memory import InMemoryToolkitLocator
from sushicore.provision.gpu.provisioning import provision_gpu_adapters
from sushicore.provision.gpu.registry import Registry

pytestmark = pytest.mark.small

_COMMIT = "d5f649b706f63b5c74e1929bc95db8de91085560"
_TOOLCHAIN = Path("toolchain")
_INSTALL = ToolkitInstall(root=Path("toolkit"), version=None)


def _spec(vendor: str, locator: InMemoryToolkitLocator) -> GpuBackendSpec:
    """Build one GpuBackendSpec whose locator is *locator*."""
    return GpuBackendSpec(
        vendor=vendor,
        probe_vendor=f"{vendor}vendor",
        locator=locator,
        adapter_option=f"UR_BUILD_ADAPTER_{vendor.upper()}",
        adapter_definitions=lambda install: {},
        adapter_target=f"ur_adapter_{vendor}",
        adapter_binaries=(f"ur_adapter_{vendor}",),
    )


def _cfg() -> SimpleNamespace:
    """Return a Linux configuration."""
    return SimpleNamespace(platform="linux", is_windows=False)


@pytest.mark.parametrize(("dry_run", "infos", "warnings"), [
    (False, [], ["Could not read the intel/llvm commit the installed SYCL toolchain was built "
                 "from; skipping every GPU adapter build."]),
    (True, ["(dry-run) would read the compiler commit and build GPU adapters."], []),
], ids=["real-run-warns", "dry-run-says-what-it-would-do"])
def test_a_missing_commit_builds_nothing_and_says_so(recording_console, dry_run, infos, warnings):
    """Check that no commit builds nothing, with a warning in a real run and an info line in a dry run."""
    registry = Registry((_spec("cuda", InMemoryToolkitLocator(_INSTALL)),))
    builder = InMemoryAdapterBuilder()

    provision_gpu_adapters(_cfg(), registry, _TOOLCHAIN, builder, dry_run=dry_run,
                           commit_reader=lambda path: None)

    assert builder.built == []
    assert recording_console.texts("info") == infos
    assert recording_console.texts("warn") == warnings


def test_a_backend_with_no_located_toolkit_is_skipped(recording_console):
    """Check that a backend whose toolkit is absent is skipped and the next one is built."""
    registry = Registry((
        _spec("cuda", InMemoryToolkitLocator(None)),
        _spec("rocm", InMemoryToolkitLocator(_INSTALL)),
    ))
    builder = InMemoryAdapterBuilder()

    provision_gpu_adapters(_cfg(), registry, _TOOLCHAIN, builder, dry_run=False,
                           commit_reader=lambda path: _COMMIT)

    assert builder.built == ["rocm"]
    assert recording_console.texts("info") == ["cuda toolkit not found; adapter build skipped."]


def test_one_built_and_one_failed_are_both_called_and_neither_raises(recording_console):
    """Check that a failing build does not stop the next one and adds no warning."""
    registry = Registry((
        _spec("cuda", InMemoryToolkitLocator(_INSTALL)),
        _spec("rocm", InMemoryToolkitLocator(_INSTALL)),
    ))
    builder = InMemoryAdapterBuilder({"cuda": True, "rocm": False})

    provision_gpu_adapters(_cfg(), registry, _TOOLCHAIN, builder, dry_run=False,
                           commit_reader=lambda path: _COMMIT)

    assert builder.built == ["cuda", "rocm"]
    assert recording_console.texts("warn") == []


def test_a_locator_that_raises_is_swallowed_and_warned(recording_console):
    """Check that a locator error becomes one warning naming its type and message."""
    registry = Registry((
        _spec("cuda", InMemoryToolkitLocator(fail_with=OSError("disk unreadable"))),))
    builder = InMemoryAdapterBuilder()

    provision_gpu_adapters(_cfg(), registry, _TOOLCHAIN, builder, dry_run=False,
                           commit_reader=lambda path: _COMMIT)

    assert builder.built == []
    assert recording_console.texts("warn") == [
        "GPU adapter provisioning failed (OSError): disk unreadable"]
