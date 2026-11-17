# test_gpu_stage.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The GPU stage and the adapter build the install steps share."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.gpu.adapter_builder_memory import InMemoryAdapterBuilder
from sushicore.provision.gpu.cuda_toolkit_installer import K_CUDA_LICENCE
from sushicore.provision.licence_consent_memory import granted_consent
from sushicore.provision.packages import AptManager
from sushicore.provision.pipeline import InstallContext, ToolchainSelection
from sushicore.provision.gpu_stage import provision_adapters_for_run
from sushicore.provision.machine_actions import MachineActions

from .recorded_gpu_stage import RecordedGpuStage


def _actions(**overrides) -> MachineActions:
    """Build machine calls that touch nothing, with *overrides* applied."""
    return MachineActions(**{"refresh_path": lambda: None, **overrides})


def _linux_context(**overrides) -> InstallContext:
    """Build an install context for a Linux run with *overrides* applied."""
    return InstallContext(cfg=ProvisionSettings(platform="linux"),
                          **{"consent": granted_consent(K_CUDA_LICENCE), **overrides})


def _windows_context(*, gpu: bool, vendor: str) -> InstallContext:
    """Build an install context for a Windows run that selects the GPU or not."""
    return InstallContext(cfg=ProvisionSettings(platform="windows"),
                          selection=ToolchainSelection(gpu=gpu), gpu_vendor=vendor,
                          consent=granted_consent(K_CUDA_LICENCE))


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
    recorded = RecordedGpuStage()
    ctx = _windows_context(gpu=True, vendor="nvidia")

    recorded.stage().provision_windows(ctx)

    assert (recorded.stacks, recorded.adapters) == (["nvidia"], [ctx])


@pytest.mark.small
def test_the_windows_gpu_stage_does_nothing_without_gpu():
    """Check that a run which did not select the GPU installs and builds nothing on Windows."""
    recorded = RecordedGpuStage()

    recorded.stage().provision_windows(_windows_context(gpu=False, vendor="nvidia"))

    assert (recorded.stacks, recorded.adapters) == ([], [])


@pytest.mark.small
def test_the_windows_gpu_stage_builds_no_adapter_when_no_gpu_is_detected():
    """Check that vendor none reaches the SDK install, which settles on the CPU path, and no build."""
    recorded = RecordedGpuStage()

    recorded.stage().provision_windows(_windows_context(gpu=True, vendor="none"))

    assert (recorded.stacks, recorded.adapters) == (["none"], [])


@pytest.mark.small
def test_the_linux_gpu_stage_installs_the_sdk_and_builds_the_adapters_when_gpu_is_selected():
    """Check that a selected GPU gets its SDK and then its adapters through apt."""
    recorded = RecordedGpuStage()
    ctx = _linux_context(selection=ToolchainSelection(gpu=True), gpu_vendor="nvidia")

    recorded.stage().provision_linux(ctx, AptManager())

    assert (recorded.stacks, recorded.adapters) == (["nvidia"], [ctx])


@pytest.mark.small
def test_the_linux_gpu_stage_does_nothing_without_gpu():
    """Check that a run which did not select the GPU installs and builds nothing on Linux."""
    recorded = RecordedGpuStage()
    ctx = _linux_context(selection=ToolchainSelection(gpu=False), gpu_vendor="nvidia")

    recorded.stage().provision_linux(ctx, AptManager())

    assert (recorded.stacks, recorded.adapters) == ([], [])


@pytest.mark.small
def test_the_linux_gpu_stage_builds_no_adapter_when_no_gpu_is_detected():
    """Check that vendor none reaches the SDK install, which settles on the CPU path, and no build."""
    recorded = RecordedGpuStage()
    ctx = _linux_context(selection=ToolchainSelection(gpu=True), gpu_vendor="none")

    recorded.stage().provision_linux(ctx, AptManager())

    assert (recorded.stacks, recorded.adapters) == (["none"], [])


@pytest.mark.small
def test_the_gpu_stage_declares_the_cuda_licence_for_an_nvidia_run_without_a_toolkit():
    """Check that a selected NVIDIA GPU with no toolkit on the machine needs the CUDA licence."""
    ctx = _windows_context(gpu=True, vendor="nvidia")

    assert RecordedGpuStage().stage().toolkit_licences(ctx) == [K_CUDA_LICENCE]


@pytest.mark.small
@pytest.mark.parametrize(("gpu", "vendor", "present"), [
    (False, "nvidia", False), (True, "amd", False), (True, "none", False), (True, "nvidia", True),
], ids=["gpu not selected", "another vendor", "no gpu", "toolkit already installed"])
def test_the_gpu_stage_declares_no_licence_when_it_installs_no_toolkit(gpu, vendor, present):
    """Check that a run the stage installs no CUDA toolkit for declares no licence."""
    ctx = _windows_context(gpu=gpu, vendor=vendor)

    assert RecordedGpuStage(toolkit_present=present).stage().toolkit_licences(ctx) == []


@pytest.mark.small
def test_the_windows_gpu_stage_installs_no_cuda_toolkit_without_consent():
    """Check that an NVIDIA run whose user did not accept the CUDA licence installs no SDK."""
    recorded = RecordedGpuStage()
    ctx = _windows_context(gpu=True, vendor="nvidia")
    ctx.consent = None

    recorded.stage().provision_windows(ctx)

    assert recorded.stacks == []


@pytest.mark.small
def test_the_linux_gpu_stage_installs_no_cuda_toolkit_without_consent():
    """Check that an NVIDIA run on apt whose user did not accept the CUDA licence installs no SDK."""
    recorded = RecordedGpuStage()
    ctx = _linux_context(selection=ToolchainSelection(gpu=True), gpu_vendor="nvidia",
                         consent=None)

    recorded.stage().provision_linux(ctx, AptManager())

    assert recorded.stacks == []
