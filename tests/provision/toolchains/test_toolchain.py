# test_toolchain.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A toolchain a test declares installs through the contract with no change to a plan."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments_memory import InMemoryDependencySource
from sushicore.provision.gpu_stage import GpuStage
from sushicore.provision.install_deps_plan import InstallServices
from sushicore.provision.machine_actions import MachineActions
from sushicore.provision.install_context import InstallContext
from sushicore.provision.toolchain_selection import ToolchainSelection
from sushicore.provision.toolchain_install import install_toolchains
from sushicore.provision.toolchains.registry import ToolchainRegistry
from sushicore.provision.toolchains.toolchain import Toolchain, ToolchainEnv

pytestmark = pytest.mark.small


class _Recording:
    """A toolchain that records its install and answers a fixed result."""

    def __init__(self, key: str, field: str, result: bool, log: list[str]) -> None:
        """Declare the toolchain *key*, selected by *field*."""
        self.key = key
        self.selection_field = field
        self._result = result
        self._log = log

    def locate(self, cfg):
        """Find nothing."""
        return None

    def licences(self, ctx):
        """Name no licence."""
        return []

    def install(self, ctx: InstallContext, env: ToolchainEnv) -> bool:
        """Record the install and answer the fixed result."""
        self._log.append(self.key)
        return self._result


def _services() -> InstallServices:
    """Build install services whose console records and whose machine runs nothing."""
    console = RecordingConsole()
    actions = MachineActions(refresh_path=lambda: None)
    return InstallServices(source=InMemoryDependencySource([]), managers=[], console=console,
                           actions=actions, gpu=GpuStage(console=console, actions=actions))


def test_install_toolchains_installs_only_the_selected_ones_in_registry_order():
    """Check that selected toolchains install in registry order and a failure is reported."""
    log: list[str] = []
    registry = ToolchainRegistry((
        _Recording("first", "install_intel_llvm", True, log),
        _Recording("skipped", "install_acpp", True, log),
        _Recording("last", "oneapi", False, log),
    ))
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"),
                         selection=ToolchainSelection(install_intel_llvm=True, oneapi=True))

    ok = install_toolchains(ctx, _services(), mgr=None, vcpkg=None, registry=registry)

    assert (log, ok) == (["first", "last"], False)


def test_a_recording_toolchain_answers_the_toolchain_contract():
    """Check that a test's own toolchain class satisfies the Toolchain protocol."""
    assert isinstance(_Recording("k", "oneapi", True, []), Toolchain)

