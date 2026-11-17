# test_install_deps.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The GPU stage of an install run is reached only when GPU is selected, and the VS tools only when needed."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments_memory import InMemoryDependencySource
from sushicore.provision.gpu.cuda_toolkit_installer import K_CUDA_LICENCE
from sushicore.provision.gpu_stage import GpuStage
from sushicore.provision.install_deps_step import InstallDepsStep
from sushicore.provision.licence_consent import Licence
from sushicore.provision.licence_consent_memory import granted_consent
from sushicore.provision.packages.base_memory import InMemoryPackageManager
from sushicore.provision.pipeline import InstallContext, StepResult, ToolchainSelection
from sushicore.provision.machine_actions import MachineActions

from ..test_gpu_stage.recorded_gpu_stage import RecordedGpuStage


def _actions(**overrides) -> MachineActions:
    """Build machine calls that touch nothing, with *overrides* applied."""
    return MachineActions(**{"refresh_path": lambda: None, **overrides})


def _windows_context(*, gpu: bool, vendor: str) -> InstallContext:
    """Build an install context for a Windows run that selects the GPU or not."""
    return InstallContext(cfg=ProvisionSettings(platform="windows"),
                          selection=ToolchainSelection(gpu=gpu), gpu_vendor=vendor)


@pytest.mark.medium
def test_a_windows_run_hands_the_gpu_stage_the_context_when_gpu_is_selected():
    """Check that a Windows install run reaches its GPU stage with the run's context."""
    recorded = RecordedGpuStage()
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
    recorded = RecordedGpuStage()
    step = InstallDepsStep(
        InMemoryDependencySource([]), managers=[], console=RecordingConsole(),
        actions=_actions(which=lambda name: "/bin/" + name, find_vcvars=lambda: Path("vcvars64.bat"),
                         install_oneapi=lambda run: True),
        gpu=recorded.stage())

    step.run(_windows_context(gpu=False, vendor="nvidia"))

    assert (recorded.stacks, recorded.adapters) == ([], [])


@pytest.mark.medium
def test_vs_build_tools_are_not_installed_when_a_visual_studio_has_the_cpp_tools():
    """Check that a found vcvars64.bat skips the winget install of the Build Tools."""
    ran = []
    step = InstallDepsStep(
        InMemoryDependencySource([]), managers=[InMemoryPackageManager(name="winget")],
        console=RecordingConsole(),
        actions=_actions(which=lambda name: "/bin/" + name,
                         find_vcvars=lambda: Path("vcvars64.bat"),
                         run_command=ran.append, install_oneapi=lambda run: True),
        gpu=RecordedGpuStage().stage())

    result = step.run(_windows_context(gpu=False, vendor="none"))

    assert (result, ran) == (StepResult.OK, [])


class _Winget(InMemoryPackageManager):
    """A winget manager that names each package's licence by a page of its own."""

    def licence_of(self, pkg: str) -> Licence:
        """Return the licence of *pkg*."""
        return Licence(pkg, f"https://licences.example/{pkg}")


K_VS_LICENCE = Licence("Microsoft.VisualStudio.2022.BuildTools",
                       "https://licences.example/Microsoft.VisualStudio.2022.BuildTools")
K_GIT_LICENCE = Licence("Git.Git", "https://licences.example/Git.Git")


def _ran(ran: list, command: list[str]) -> int:
    """Record *command* and answer the exit code 0 of a command that succeeded."""
    ran.append(command)
    return 0


def _vs_missing_step(ran: list, gpu: GpuStage | None = None) -> InstallDepsStep:
    """Build a Windows step whose machine has no Visual Studio C++ tools and records commands."""
    return InstallDepsStep(
        InMemoryDependencySource([]), managers=[_Winget(name="winget")],
        console=RecordingConsole(),
        actions=_actions(which=lambda name: "/bin/" + name, find_vcvars=lambda: None,
                         run_command=lambda command: _ran(ran, command),
                         install_oneapi=lambda run: True),
        gpu=gpu or RecordedGpuStage().stage())


@pytest.mark.medium
def test_vs_build_tools_get_the_agreement_flags_after_consent():
    """Check that a consented Build Tools install hands winget both agreement flags."""
    ran = []
    ctx = _windows_context(gpu=False, vendor="none")
    ctx.consent = granted_consent(K_VS_LICENCE)

    _vs_missing_step(ran).run(ctx)

    assert {"--accept-package-agreements", "--accept-source-agreements"} <= set(ran[0])


@pytest.mark.medium
def test_vs_build_tools_are_not_installed_without_consent():
    """Check that a Build Tools install no consent covers runs nothing and fails the step."""
    ran = []

    result = _vs_missing_step(ran).run(_windows_context(gpu=False, vendor="none"))

    assert (result, ran) == (StepResult.FAILED, [])


@pytest.mark.medium
def test_the_step_declares_every_licence_its_windows_run_needs():
    """Check that a missing Build Tools and an NVIDIA GPU declare the Build Tools and CUDA licences."""
    step = _vs_missing_step([])

    needed = step.licences(_windows_context(gpu=True, vendor="nvidia"))

    assert set(needed) == {K_CUDA_LICENCE, K_VS_LICENCE}


@pytest.mark.medium
def test_the_step_declares_no_cuda_licence_when_the_release_is_already_installed():
    """Check that an NVIDIA run whose toolkit is on the machine declares no CUDA licence."""
    step = _vs_missing_step([], gpu=RecordedGpuStage(toolkit_present=True).stage())

    needed = step.licences(_windows_context(gpu=True, vendor="nvidia"))

    assert K_CUDA_LICENCE not in needed
