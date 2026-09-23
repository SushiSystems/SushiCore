# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""``InstallDepsStep`` reaches ``provision_adapters_for_run`` only when GPU is selected."""

from __future__ import annotations

from sushicore.provision import steps as steps_mod
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments import IDependencySource
from sushicore.provision.packages import LinuxPackageManager
from sushicore.provision.packages import install_gpu_stack as _real_install_gpu_stack
from sushicore.provision.pipeline import InstallContext, StepResult, ToolchainSelection
from sushicore.provision.steps import InstallDepsStep, provision_adapters_for_run


class MemorySource(IDependencySource):
    """Serves a fixed, empty dependency list."""

    def all(self):
        """Return no dependencies."""
        return []


class _FakeAptManager(LinuxPackageManager):
    """An always-available apt manager that installs nothing for real."""

    name = "apt"

    def available(self) -> bool:
        """Report present, unconditionally."""
        return True

    def is_installed(self, pkg: str) -> bool:
        """Report every package as already installed."""
        return True

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Record no work and report success."""
        return True

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Record no work and report success."""
        return True


def test_provision_adapters_for_run_skips_without_a_resolved_llvm_root(
        monkeypatch, recording_console):
    calls = []
    monkeypatch.setattr(
        steps_mod, "provision_gpu_adapters",
        lambda cfg, registry, root, builder, dry_run: calls.append(root))
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"))

    provision_adapters_for_run(ctx)

    assert calls == []
    infos = [args[0] for name, args in recording_console.calls if name == "info"]
    assert any("GPU adapter build skipped" in i for i in infos)


def test_provision_adapters_for_run_uses_the_resolved_llvm_root(
        monkeypatch, tmp_path, recording_console):
    calls = []
    monkeypatch.setattr(
        steps_mod, "provision_gpu_adapters",
        lambda cfg, registry, root, builder, dry_run: calls.append(root))
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"))
    ctx.resolved_paths["llvm_root"] = str(tmp_path)

    provision_adapters_for_run(ctx)

    assert calls == [tmp_path]


def _patch_heavy_windows_steps(monkeypatch, llvm_root: str) -> None:
    """Stub every Windows sub-step except the GPU block, and mark the toolchain resolved."""
    monkeypatch.setattr(InstallDepsStep, "_install_portable_tools",
                        lambda self, ctx, direct: True)
    monkeypatch.setattr(InstallDepsStep, "_install_git",
                        lambda self, ctx, winget, direct: True)
    monkeypatch.setattr(InstallDepsStep, "_install_vcpkg_ports",
                        lambda self, ctx, vcpkg: ([], True))
    monkeypatch.setattr(InstallDepsStep, "_install_vs_build_tools",
                        lambda self, ctx, winget: True)
    monkeypatch.setattr(InstallDepsStep, "_install_toolchains",
                        lambda self, ctx, mgr, vcpkg: ctx.resolved_paths.update(
                            {"llvm_root": llvm_root}))
    monkeypatch.setattr(steps_mod.oneapi, "install_oneapi", lambda ctx: True)
    monkeypatch.setattr(steps_mod, "install_gpu_stack", lambda cfg, vendor, dry_run: True)
    monkeypatch.setattr(steps_mod.probe, "detect_gpu_vendor", lambda: "nvidia")


def test_run_windows_reaches_provision_adapters_for_run_when_gpu_is_selected(
        monkeypatch, tmp_path):
    _patch_heavy_windows_steps(monkeypatch, str(tmp_path))
    calls = []
    monkeypatch.setattr(steps_mod, "provision_adapters_for_run", calls.append)

    step = InstallDepsStep(MemorySource(), managers=[])
    ctx = InstallContext(cfg=ProvisionSettings(platform="windows"),
                         selection=ToolchainSelection(gpu=True))

    result = step._run_windows(ctx)

    assert result is StepResult.OK
    assert calls == [ctx]


def test_run_windows_skips_provision_adapters_for_run_without_gpu(monkeypatch, tmp_path):
    _patch_heavy_windows_steps(monkeypatch, str(tmp_path))
    calls = []
    monkeypatch.setattr(steps_mod, "provision_adapters_for_run", calls.append)

    step = InstallDepsStep(MemorySource(), managers=[])
    ctx = InstallContext(cfg=ProvisionSettings(platform="windows"),
                         selection=ToolchainSelection(gpu=False))

    step._run_windows(ctx)

    assert calls == []


def _patch_heavy_linux_steps(monkeypatch, llvm_root: str) -> None:
    """Stub the toolchain install so ``ctx.resolved_paths["llvm_root"]`` is set."""
    monkeypatch.setattr(InstallDepsStep, "_install_toolchains",
                        lambda self, ctx, mgr, vcpkg: ctx.resolved_paths.update(
                            {"llvm_root": llvm_root}))
    monkeypatch.setattr(steps_mod, "install_gpu_stack", lambda cfg, vendor, dry_run: True)
    monkeypatch.setattr(steps_mod.probe, "detect_gpu_vendor", lambda: "nvidia")


def test_run_linux_reaches_provision_adapters_for_run_when_gpu_is_selected(
        monkeypatch, tmp_path, recording_console):
    _patch_heavy_linux_steps(monkeypatch, str(tmp_path))
    calls = []
    monkeypatch.setattr(steps_mod, "provision_adapters_for_run", calls.append)

    step = InstallDepsStep(MemorySource(), managers=[_FakeAptManager()])
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"),
                         selection=ToolchainSelection(gpu=True))

    result = step._run_linux(ctx)

    assert result is StepResult.OK
    assert calls == [ctx]


def test_run_linux_skips_provision_adapters_for_run_without_gpu(
        monkeypatch, tmp_path, recording_console):
    _patch_heavy_linux_steps(monkeypatch, str(tmp_path))
    calls = []
    monkeypatch.setattr(steps_mod, "provision_adapters_for_run", calls.append)

    step = InstallDepsStep(MemorySource(), managers=[_FakeAptManager()])
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"),
                         selection=ToolchainSelection(gpu=False))

    step._run_linux(ctx)

    assert calls == []


def test_run_windows_with_no_gpu_provisions_nothing(monkeypatch, tmp_path, recording_console):
    _patch_heavy_windows_steps(monkeypatch, str(tmp_path))
    monkeypatch.setattr(steps_mod, "install_gpu_stack", _real_install_gpu_stack)
    calls = []
    monkeypatch.setattr(steps_mod, "provision_adapters_for_run", calls.append)

    step = InstallDepsStep(MemorySource(), managers=[])
    ctx = InstallContext(cfg=ProvisionSettings(platform="windows"),
                         selection=ToolchainSelection(gpu=True), gpu_vendor="none")

    step._run_windows(ctx)

    assert calls == []
    infos = [args[0] for name, args in recording_console.calls if name == "info"]
    assert any("No discrete GPU detected" in i for i in infos)


def test_run_linux_with_no_gpu_provisions_nothing(monkeypatch, tmp_path, recording_console):
    _patch_heavy_linux_steps(monkeypatch, str(tmp_path))
    monkeypatch.setattr(steps_mod, "install_gpu_stack", _real_install_gpu_stack)
    calls = []
    monkeypatch.setattr(steps_mod, "provision_adapters_for_run", calls.append)

    step = InstallDepsStep(MemorySource(), managers=[_FakeAptManager()])
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"),
                         selection=ToolchainSelection(gpu=True), gpu_vendor="none")

    step._run_linux(ctx)

    assert calls == []
    infos = [args[0] for name, args in recording_console.calls if name == "info"]
    assert any("No discrete GPU detected" in i for i in infos)
