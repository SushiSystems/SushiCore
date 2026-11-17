# install_deps_step.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Installs the missing manifest dependencies and the system toolchain."""

from __future__ import annotations

from typing import Any, final

from .default_console import console_or_default
from .download_checking import DownloadChecking
from .download_verifier import DEFAULT_VERIFIER_SLOT, DownloadVerifier
from .fragments import IDependencySource
from .gpu_stage import GpuStage
from .install_deps_plan import INSTALL_PLANS, InstallServices
from .licence_consent import Licence
from .machine_actions import MachineActions
from .packages import IPackageManager
from .install_context import InstallContext
from .step import Step
from .step_result import StepResult
from .target import target_of


@final
class InstallDepsStep(Step):
    """Install missing manifest dependencies and system toolchain."""

    name = "install-deps"

    def __init__(self, source: IDependencySource, managers: list[IPackageManager],
                 *, console: Any = None, actions: MachineActions | None = None,
                 gpu: GpuStage | None = None,
                 verifier: DownloadChecking | None = None) -> None:
        """Wire the dependency source, the package managers and the machine.

        Args:
            console: The console the step prints through.
            actions: The machine calls; the real ones when omitted.
            gpu: The GPU part of the run; built from *console* and *actions* when omitted.
            verifier: Checks the run's downloads, and the one the managers were built with; built
                from the source's digests when omitted.
        """
        console = console_or_default(console, "InstallDepsStep")
        self._source = source
        self._verifier = verifier
        actions = actions or MachineActions()
        self._services = InstallServices(
            source=source, managers=managers, console=console, actions=actions,
            gpu=gpu or GpuStage(console=console, actions=actions))

    def licences(self, ctx: InstallContext) -> list[Licence]:
        """Returns the third-party licences this step's installers need for *ctx*.

        Read after detection, so *ctx* already holds what the machine has.
        """
        needed: list[Licence] = self._services.gpu.toolkit_licences(ctx)
        return INSTALL_PLANS.plan_for(target_of(ctx.cfg)).licences(ctx, needed, self._services)

    def run(self, ctx: InstallContext) -> StepResult:
        """Run the install routine of this platform with the fragments' digests bound.

        Raises:
            DigestMismatchError: A download's SHA-256 is not the one its entry pins.
        """
        platform = ctx.cfg.platform
        verifier = self._verifier or DownloadVerifier(self._source.digests(platform),
                                                      self._source.downloads(platform))
        ctx.verifier = verifier
        with DEFAULT_VERIFIER_SLOT.holding(verifier):
            return INSTALL_PLANS.plan_for(target_of(ctx.cfg)).run(ctx, self._services)
