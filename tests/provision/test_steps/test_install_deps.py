# test_install_deps.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The GPU part of an install run happens only when GPU is selected, and the VS tools only when needed."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments_memory import InMemoryDependencySource
from sushicore.provision.gpu.adapter_builder_memory import InMemoryAdapterBuilder
from sushicore.provision.packages import IPackageManager
from sushicore.provision.pipeline import InstallContext, StepResult, ToolchainSelection
from sushicore.provision.steps import (
    GpuStage,
    InstallDepsStep,
    MachineActions,
    provision_adapters_for_run,
)


def _actions(**overrides) -> MachineActions:
    """Build machine calls that touch nothing, with *overrides* applied."""
    return MachineActions(**{"refresh_path": lambda: None, **overrides})


def _linux_context(**overrides) -> InstallContext:
    """Build an install context for a Linux run with *overrides* applied."""
    return InstallContext(cfg=ProvisionSettings(platform="linux"), **overrides)


def _windows_context(*, gpu: bool, vendor: str) -> InstallContext:
    """Build an install context for a Windows run that selects the GPU or not."""
    return InstallContext(cfg=ProvisionSettings(platform="windows"),
                          selection=ToolchainSelection(gpu=gpu), gpu_vendor=vendor)


class _Recorded:
    """The two GPU actions of a stage, recording what they were asked for."""

    def __init__(self) -> None:
        """Start with nothing recorded."""
        self.stacks: list[str] = []
        self.adapters: list[InstallContext] = []

    def stage(self) -> GpuStage:
        """Build a stage whose SDK install and adapter build record into this object."""
        return GpuStage(
            console=RecordingConsole(), actions=_actions(),
            install_stack=lambda cfg, vendor, dry_run: self.stacks.append(vendor) or True,
            provision_adapters=self.adapters.append)


@pytest.mark.small
def test_provision_adapters_for_run_skips_without_a_resolved_llvm_root():
    """Check that no adapter is built, and the skip is said, when no llvm root is known."""
    built = []
    out = RecordingConsole()

    provision_adapters_for_run(
        _linux_context(), console=out, actions=_actions(resolve_config=lambda cfg, gpu=False: {}),
        build_adapters=lambda *args: built.append(args))

    assert built == []
    assert any("GPU adapter build skipped" in text for text in out.texts("info"))


@pytest.mark.small
def test_provision_adapters_for_run_uses_the_resolved_llvm_root():
    """Check that the adapters are built against the llvm root the install resolved."""
    built = []
    ctx = _linux_context()
    ctx.resolved_paths["llvm_root"] = "/opt/llvm"

    provision_adapters_for_run(
        ctx, console=RecordingConsole(),
        actions=_actions(resolve_config=lambda cfg, gpu=False: {}),
        build_adapters=lambda cfg, registry, root, builder, dry_run: built.append(root))

    assert built == [Path("/opt/llvm")]


@pytest.mark.small
def test_provision_adapters_for_run_uses_a_toolchain_already_on_the_machine():
    """Check that a run which installed no toolchain builds against the probed llvm root."""
    built = []

    provision_adapters_for_run(
        _linux_context(), console=RecordingConsole(),
        actions=_actions(resolve_config=lambda cfg, gpu=False: {"llvm_root": "/usr/lib/llvm"}),
        build_adapters=lambda cfg, registry, root, builder, dry_run: built.append(root))

    assert built == [Path("/usr/lib/llvm")]


@pytest.mark.small
def test_provision_adapters_for_run_drops_probed_keys_the_settings_do_not_hold():
    """Check that a probed key with no field on the settings does not stop the adapter build."""
    built = []
    probed = {"llvm_root": "/opt/llvm", "cxx": "clang++", "not_a_setting": "x"}

    provision_adapters_for_run(
        _linux_context(), console=RecordingConsole(),
        actions=_actions(resolve_config=lambda cfg, gpu=False: probed),
        build_adapters=lambda cfg, registry, root, builder, dry_run: built.append(cfg.cxx))

    assert built == ["clang++"]


@pytest.mark.small
def test_provision_adapters_for_run_hands_the_builder_it_made_to_the_build():
    """Check that the build receives the builder made from the probed configuration."""
    builder = InMemoryAdapterBuilder()
    received = []
    ctx = _linux_context()
    ctx.resolved_paths["llvm_root"] = "/opt/llvm"

    provision_adapters_for_run(
        ctx, console=RecordingConsole(),
        actions=_actions(resolve_config=lambda cfg, gpu=False: {}),
        make_builder=lambda cfg: builder,
        build_adapters=lambda cfg, registry, root, made, dry_run: received.append(made))

    assert received == [builder]


@pytest.mark.small
def test_the_windows_gpu_stage_installs_the_sdk_and_builds_the_adapters_when_gpu_is_selected():
    """Check that a selected GPU gets its SDK and then its adapters on Windows."""
    recorded = _Recorded()
    ctx = _windows_context(gpu=True, vendor="nvidia")

    recorded.stage().provision_windows(ctx)

    assert (recorded.stacks, recorded.adapters) == (["nvidia"], [ctx])


@pytest.mark.small
def test_the_windows_gpu_stage_does_nothing_without_gpu():
    """Check that a run which did not select the GPU installs and builds nothing on Windows."""
    recorded = _Recorded()

    recorded.stage().provision_windows(_windows_context(gpu=False, vendor="nvidia"))

    assert (recorded.stacks, recorded.adapters) == ([], [])


@pytest.mark.small
def test_the_windows_gpu_stage_builds_no_adapter_when_no_gpu_is_detected():
    """Check that vendor none reaches the SDK install, which settles on the CPU path, and no build."""
    recorded = _Recorded()

    recorded.stage().provision_windows(_windows_context(gpu=True, vendor="none"))

    assert (recorded.stacks, recorded.adapters) == (["none"], [])


@pytest.mark.small
def test_the_linux_gpu_stage_installs_the_sdk_and_builds_the_adapters_when_gpu_is_selected():
    """Check that a selected GPU gets its SDK and then its adapters through apt."""
    recorded = _Recorded()
    ctx = _linux_context(selection=ToolchainSelection(gpu=True), gpu_vendor="nvidia")

    recorded.stage().provision_linux(ctx, "apt")

    assert (recorded.stacks, recorded.adapters) == (["nvidia"], [ctx])


@pytest.mark.small
def test_the_linux_gpu_stage_does_nothing_without_gpu():
    """Check that a run which did not select the GPU installs and builds nothing on Linux."""
    recorded = _Recorded()
    ctx = _linux_context(selection=ToolchainSelection(gpu=False), gpu_vendor="nvidia")

    recorded.stage().provision_linux(ctx, "apt")

    assert (recorded.stacks, recorded.adapters) == ([], [])


@pytest.mark.small
def test_the_linux_gpu_stage_builds_no_adapter_when_no_gpu_is_detected():
    """Check that vendor none reaches the SDK install, which settles on the CPU path, and no build."""
    recorded = _Recorded()
    ctx = _linux_context(selection=ToolchainSelection(gpu=True), gpu_vendor="none")

    recorded.stage().provision_linux(ctx, "apt")

    assert (recorded.stacks, recorded.adapters) == (["none"], [])


@pytest.mark.medium
def test_a_windows_run_hands_the_gpu_stage_the_context_when_gpu_is_selected():
    """Check that a Windows install run reaches its GPU stage with the run's context."""
    recorded = _Recorded()
    ctx = _windows_context(gpu=True, vendor="nvidia")
    step = InstallDepsStep(
        InMemoryDependencySource([]), managers=[], console=RecordingConsole(),
        actions=_actions(which=lambda name: "/bin/" + name, find_vcvars=lambda: Path("vcvars64.bat"),
                         install_oneapi=lambda run: True),
        gpu=recorded.stage())

    result = step.run(ctx)

    assert (result, recorded.adapters) == (StepResult.OK, [ctx])


@pytest.mark.medium
def test_a_windows_run_without_gpu_leaves_the_gpu_stage_with_nothing_to_install():
    """Check that a Windows install run without the GPU installs and builds no GPU part."""
    recorded = _Recorded()
    step = InstallDepsStep(
        InMemoryDependencySource([]), managers=[], console=RecordingConsole(),
        actions=_actions(which=lambda name: "/bin/" + name, find_vcvars=lambda: Path("vcvars64.bat"),
                         install_oneapi=lambda run: True),
        gpu=recorded.stage())

    step.run(_windows_context(gpu=False, vendor="nvidia"))

    assert (recorded.stacks, recorded.adapters) == ([], [])


class _WingetWithoutBuildTools(IPackageManager):
    """A winget that is present, reports every package missing and installs nothing."""

    name = "winget"

    def available(self) -> bool:
        """Report present."""
        return True

    def is_installed(self, pkg: str) -> bool:
        """Report every package as missing."""
        return False

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Report success without installing."""
        return True

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Report success without removing."""
        return True


@pytest.mark.medium
def test_vs_build_tools_are_not_installed_when_a_visual_studio_has_the_cpp_tools():
    """Check that a found vcvars64.bat skips the winget install of the Build Tools."""
    ran = []
    step = InstallDepsStep(
        InMemoryDependencySource([]), managers=[_WingetWithoutBuildTools()],
        console=RecordingConsole(),
        actions=_actions(which=lambda name: "/bin/" + name,
                         find_vcvars=lambda: Path("vcvars64.bat"),
                         run_command=ran.append, install_oneapi=lambda run: True),
        gpu=_Recorded().stage())

    result = step.run(_windows_context(gpu=False, vendor="none"))

    assert (result, ran) == (StepResult.OK, [])
