# gpu_stage.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The GPU stage of an install run: the compute SDK, then the adapter builds."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Callable, final

from .default_console import console_or_default
from .gpu.adapter_builder import AdapterBuilder, SubprocessBuildStepExecutor
from .gpu.cuda_toolkit_installer import K_CUDA_LICENCE
from .gpu.provisioning import provision_gpu_adapters
from .gpu.registry import DEFAULT_REGISTRY
from .adapter_provisioner import AdapterProvisioner
from .config import ProvisionConfig
from .gpu_machine import GpuMachine
from .licence_consent import Licence, is_accepted
from .packages import LinuxPackageManager, install_gpu_stack
from .install_context import InstallContext
from .provision_console import ProvisionConsole


def _subprocess_builder(cfg: ProvisionConfig, console: ProvisionConsole) -> AdapterBuilder:
    """Return the adapter builder that runs its commands as processes printing through *console*."""
    return AdapterBuilder(cfg=cfg, runner=SubprocessBuildStepExecutor(console), console=console)


def provision_adapters_for_run(
        ctx: InstallContext, *, console: ProvisionConsole | None = None,
        actions: GpuMachine,
        make_builder: Callable[[ProvisionConfig, ProvisionConsole], AdapterBuilder] = _subprocess_builder,
        build_adapters: AdapterProvisioner | None = None) -> None:
    """Build every located GPU backend's Unified Runtime adapter for this run.

    Args:
        console: The console the skip message is printed through.
        actions: The machine calls the run reads.
        make_builder: Builds the adapter builder from the probed configuration and the console.
        build_adapters: Builds the adapters of one toolchain; defaults to
            :func:`sushicore.provision.gpu.provisioning.provision_gpu_adapters`.
    """
    console = console_or_default(console, "provision_adapters_for_run")
    build_adapters = build_adapters or provision_gpu_adapters
    actions.refresh_path()
    probed = actions.resolve_config(ctx.cfg, gpu=ctx.gpu)
    llvm_root = ctx.resolved_paths.get("llvm_root") or probed.get("llvm_root")
    if not llvm_root:
        console.info("No intel/llvm toolchain installed; GPU adapter build skipped.")
        return
    held = {field.name for field in dataclasses.fields(ctx.cfg)}
    cfg = dataclasses.replace(ctx.cfg, **{key: value for key, value in probed.items() if key in held})
    build_adapters(cfg, DEFAULT_REGISTRY, Path(llvm_root), make_builder(cfg, console), ctx.dry_run,
                   console=console)


def _nvidia_toolkit_present(ctx: InstallContext) -> bool:
    """Return whether a CUDA toolkit is already found on this machine for the run's platform."""
    spec = DEFAULT_REGISTRY.for_probe_vendor("nvidia")
    return spec is not None and spec.locator.locate(ctx.cfg) is not None


def _resolve_gpu_vendor(ctx: InstallContext, detect: Callable[[], str]) -> str:
    """Return the GPU vendor the detect step recorded, probing the machine when it did not."""
    ctx.gpu_vendor = ctx.gpu_vendor or detect() or "none"
    return ctx.gpu_vendor


@final
class GpuStage:
    """The GPU part of an install run: the compute SDK, then the adapter builds.

    Args:
        console: The console the warnings are printed through.
        actions: The machine calls the stage reads.
        install_stack: Installs the compute SDK of a vendor; the packages' default when omitted.
        provision_adapters: Builds the adapters for a run; :func:`provision_adapters_for_run`.
        toolkit_present: Whether the run's NVIDIA toolkit is already on the machine.
    """

    def __init__(self, *, console: ProvisionConsole | None = None, actions: GpuMachine,
                 install_stack: Callable[[ProvisionConfig, str, bool], bool] | None = None,
                 provision_adapters: Callable[[InstallContext], None] | None = None,
                 toolkit_present: Callable[[InstallContext], bool] | None = None,
                 ) -> None:
        """Wire the console, the machine calls and the GPU actions."""
        console = console_or_default(console, "GpuStage")
        self._console = console
        self._toolkit_present = toolkit_present or (lambda ctx: _nvidia_toolkit_present(ctx))
        self._actions = actions
        self._install_stack = install_stack or (
            lambda cfg, vendor, dry_run: install_gpu_stack(
                cfg, vendor, dry_run, console=self._console))
        self._provision_adapters = provision_adapters or (
            lambda ctx: provision_adapters_for_run(
                ctx, console=self._console, actions=self._actions))

    def toolkit_licences(self, ctx: InstallContext) -> list[Licence]:
        """Returns the licences the toolkit this stage installs for *ctx* needs; empty when none."""
        return [K_CUDA_LICENCE] if self._installs_toolkit(ctx) else []

    def provision_linux(self, ctx: InstallContext, manager: LinuxPackageManager) -> None:
        """Install the GPU SDK through *manager*, then build the adapters.

        Nothing is installed when the run did not select the GPU; the SDK is automated
        for the managers that say so.
        """
        vendor = _resolve_gpu_vendor(ctx, self._actions.detect_vendor) if ctx.gpu else "none"
        if ctx.gpu and manager.automates_gpu_sdk:
            if not self._install(ctx, vendor) and vendor != "none":
                message = (f"GPU compute SDK for '{vendor}' was not installed — "
                           f"the build will fall back to the CPU (SPIR/OpenCL) path. "
                           f"See the log above for the failing command.")
                self._console.error(message)
                ctx.warnings.append(message)
        elif ctx.gpu and vendor == "none":
            self._install(ctx, vendor)
        elif ctx.gpu:
            self._console.warn(f"GPU SDK auto-install for '{vendor}' is only "
                               f"automated on apt; install it manually on {manager.name}.")
        if vendor != "none":
            self._provision_adapters(ctx)

    def provision_windows(self, ctx: InstallContext) -> None:
        """Install the GPU SDK, then build the adapters, when the run selected the GPU."""
        if not ctx.gpu:
            return
        vendor = _resolve_gpu_vendor(ctx, self._actions.detect_vendor)
        self._install(ctx, vendor)
        if vendor != "none":
            self._provision_adapters(ctx)

    def _installs_toolkit(self, ctx: InstallContext) -> bool:
        """Report whether this run installs a CUDA toolkit: an NVIDIA GPU, none found yet."""
        vendor = ctx.gpu_vendor or self._actions.detect_vendor()
        return ctx.gpu and vendor == "nvidia" and not self._toolkit_present(ctx)

    def _install(self, ctx: InstallContext, vendor: str) -> bool:
        """Install the SDK of *vendor*, leaving a toolkit the user did not consent to alone."""
        if (self._installs_toolkit(ctx) and not ctx.dry_run
                and not is_accepted(ctx.consent, K_CUDA_LICENCE)):
            self._console.error(f"CUDA needs consent to {K_CUDA_LICENCE.name}: "
                                f"{K_CUDA_LICENCE.link}")
            return False
        return self._install_stack(ctx.cfg, vendor, ctx.dry_run)
