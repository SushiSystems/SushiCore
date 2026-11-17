# windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The Windows target."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, MutableMapping, Sequence, final

from ..config import ProvisionConfig
from .base import K_WINDOWS, ITarget, M

#: Work roots longer than this push fetched object paths past MAX_PATH.
K_MAX_WORK_ROOT_LENGTH = 60


@final
class WindowsTarget(ITarget):
    """Targets Windows: PE names, vcpkg ports, MSVC and a bootstrap batch file."""

    @property
    def name(self) -> str:
        """Return ``windows``."""
        return K_WINDOWS

    @property
    def clang_executable(self) -> str:
        """Return ``clang++.exe``."""
        return "clang++.exe"

    @property
    def nvcc_executable(self) -> str:
        """Return ``nvcc.exe``."""
        return "nvcc.exe"

    @property
    def python_executable(self) -> str:
        """Return ``python``."""
        return "python"

    @property
    def vcpkg_executable(self) -> str:
        """Return ``vcpkg.exe``."""
        return "vcpkg.exe"

    @property
    def vcpkg_triplet(self) -> str:
        """Return ``x64-windows``."""
        return "x64-windows"

    @property
    def acpp_launcher(self) -> str:
        """Return ``acpp.bat``."""
        return "acpp.bat"

    @property
    def intel_llvm_asset(self) -> str:
        """Return ``sycl_windows.tar.gz``."""
        return "sycl_windows.tar.gz"

    @property
    def searches_system_prefixes(self) -> bool:
        """Return False: Windows toolchains are found on PATH and under fixed install roots."""
        return False

    @property
    def system_prerequisites_note(self) -> str:
        """Return the sentence naming the C++ host compiler, git and the GPU toolkit."""
        return ("System prerequisites kept outside that folder: the C++ "
                "host compiler (Visual Studio Build Tools + Windows SDK), "
                "git, and the toolkit for the detected GPU.")

    @property
    def no_compiler_detail(self) -> str:
        """Return the detail of a compiler check that found no MSVC, clang++ or g++."""
        return "no MSVC (VSINSTALLDIR/vs_vcvars), clang++ or g++ found"

    @property
    def adapter_install_subdir(self) -> str:
        """Return ``bin``."""
        return "bin"

    def adapter_binary_patterns(self, base_name: str) -> list[str]:
        """Return the DLL name of *base_name*."""
        return [f"{base_name}.dll"]

    def adapter_compiler_args(self, toolchain_root: Path) -> list[str]:
        """Return the arguments that build the adapter with the bundle's clang-cl and lld-link."""
        bin_dir = toolchain_root / "bin"
        clang_cl = bin_dir / "clang-cl.exe"
        return [
            f"-DCMAKE_C_COMPILER={clang_cl}",
            f"-DCMAKE_CXX_COMPILER={clang_cl}",
            f"-DCMAKE_LINKER={bin_dir / 'lld-link.exe'}",
        ]

    def adapter_build_environment(self, cfg: ProvisionConfig, console: Any) -> dict[str, str]:
        """Return the environment with the Visual Studio developer shell merged in, when found."""
        from sushicore.build_env import merge_env, snapshot_windows
        snapshot = snapshot_windows(cfg, console)
        if snapshot is None:
            return dict(os.environ)
        return merge_env(os.environ, snapshot)

    def work_root_fits(self, work_root: Path, warn: Callable[[str], None]) -> bool:
        """Report whether *work_root* stays under the length that avoids the long-path failure."""
        length = len(str(work_root.absolute()))
        if length > K_MAX_WORK_ROOT_LENGTH:
            warn(f"Adapter build root is {length} characters, "
                 f"over the {K_MAX_WORK_ROOT_LENGTH} limit that avoids "
                 f"Windows' long-path ninja failure: {work_root}")
            return False
        return True

    def host_compilers(self, cfg: ProvisionConfig) -> list[tuple[str, str]]:
        """Return MSVC, from the developer shell or the configured vcvars script, when present."""
        dev_shell = os.environ.get("VSINSTALLDIR")
        configured = cfg.expand(cfg.vs_vcvars) if cfg.vs_vcvars else ""
        found, info = (True, dev_shell) if dev_shell else (
            bool(configured) and Path(configured).is_file(), configured)
        return [("MSVC", info)] if found else []

    def vcpkg_fallback_ports(self, apt_packages: list[str], vcpkg_ports: list[str]) -> list[str]:
        """Return no ports: on Windows vcpkg is the primary manager, not a fallback."""
        return []

    def bootstrap_vcpkg(self, root: Path, drain: Callable[[list[str], bool], int],
                        dry_run: bool) -> int:
        """Run ``bootstrap-vcpkg.bat`` through cmd."""
        bootstrap = root / "bootstrap-vcpkg.bat"
        return drain(["cmd", "/c", str(bootstrap), "-disableMetrics"], dry_run)

    def dependency_manager(self, managers: Sequence[M]) -> M | None:
        """Return the vcpkg manager among *managers*, if wired in."""
        return next((manager for manager in managers if manager.name == "vcpkg"), None)

    def acpp_skip_notes(self, llvm_version: str) -> list[str]:
        """Return the lines naming the command that fetches LLVM and why the bundle cannot."""
        return [
            "Install it anytime with [cmd]sr setup acpp[/cmd] — "
            f"that downloads LLVM {llvm_version} (~2-3 GB) into the "
            "deps folder and builds acpp, no prompt.",
            "Note: the intel/llvm bundle cannot supply this LLVM — it ships "
            "a compiler, not the LLVM cmake/dev files acpp needs.",
        ]

    def acpp_configure_args(self, vcpkg_toolchain_file: Path) -> list[str]:
        """Return the toolchain-file argument when the vcpkg toolchain file exists."""
        if vcpkg_toolchain_file.is_file():
            return [f"-DCMAKE_TOOLCHAIN_FILE={vcpkg_toolchain_file}"]
        return []

    def prepare_acpp_environment(self, env: MutableMapping[str, str],
                                 find_rc_dir: Callable[[], str]) -> None:
        """Put the SDK's resource compiler directory on PATH, which clang-cl needs for manifests."""
        rc_dir = find_rc_dir()
        if rc_dir and rc_dir.lower() not in env.get("PATH", "").lower():
            env["PATH"] = rc_dir + os.pathsep + env.get("PATH", "")
