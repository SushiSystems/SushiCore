# linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The Linux target."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, MutableMapping, Sequence, final

from ..config import ProvisionConfig
from .base import K_LINUX, ITarget, M

#: The Linux managers that can answer whether a manifest package is installed, in the order asked.
K_LINUX_MANAGERS = ("apt", "dnf", "yum", "pacman", "zypper")


@final
class LinuxTarget(ITarget):
    """Targets Linux: ELF names, distro packages and a bootstrap script run in place."""

    @property
    def name(self) -> str:
        """Return ``linux``."""
        return K_LINUX

    @property
    def clang_executable(self) -> str:
        """Return ``clang++``."""
        return "clang++"

    @property
    def nvcc_executable(self) -> str:
        """Return ``nvcc``."""
        return "nvcc"

    @property
    def python_executable(self) -> str:
        """Return ``python3``."""
        return "python3"

    @property
    def vcpkg_executable(self) -> str:
        """Return ``vcpkg``."""
        return "vcpkg"

    @property
    def vcpkg_triplet(self) -> str:
        """Return ``x64-linux``."""
        return "x64-linux"

    @property
    def acpp_launcher(self) -> str:
        """Return ``acpp``."""
        return "acpp"

    @property
    def intel_llvm_asset(self) -> str:
        """Return ``sycl_linux.tar.gz``."""
        return "sycl_linux.tar.gz"

    @property
    def searches_system_prefixes(self) -> bool:
        """Return True: oneAPI and the CUDA toolkit install under well-known prefixes."""
        return True

    @property
    def system_prerequisites_note(self) -> str:
        """Return the sentence naming the host compiler, the -dev packages and git."""
        return ("System prerequisites kept outside that folder: the host "
                "compiler (gcc) plus the -dev packages (hwloc, gtest, "
                "opencl), git, and the toolkit for the detected GPU.")

    @property
    def no_compiler_detail(self) -> str:
        """Return the detail of a compiler check that found neither clang++ nor g++."""
        return "no clang++ or g++ on PATH"

    @property
    def adapter_install_subdir(self) -> str:
        """Return ``lib``."""
        return "lib"

    def adapter_binary_patterns(self, base_name: str) -> list[str]:
        """Return the shared-object glob of *base_name*."""
        return [f"lib{base_name}.so*"]

    def adapter_compiler_args(self, toolchain_root: Path) -> list[str]:
        """Return no arguments: the default compiler builds the adapter."""
        return []

    def adapter_build_environment(self, cfg: ProvisionConfig, console: Any) -> dict[str, str]:
        """Return a copy of the process environment."""
        return dict(os.environ)

    def work_root_fits(self, work_root: Path, warn: Callable[[str], None]) -> bool:
        """Return True: Linux has no path-length limit the build trips on."""
        return True

    def host_compilers(self, cfg: ProvisionConfig) -> list[tuple[str, str]]:
        """Return no compilers: the PATH ones are all there are."""
        return []

    def vcpkg_fallback_ports(self, apt_packages: list[str], vcpkg_ports: list[str]) -> list[str]:
        """Return *vcpkg_ports* when the dependency has no distro package, else none."""
        return [] if apt_packages else vcpkg_ports

    def bootstrap_vcpkg(self, root: Path, drain: Callable[[list[str], bool], int],
                        dry_run: bool) -> int:
        """Make ``bootstrap-vcpkg.sh`` executable and run it."""
        bootstrap = root / "bootstrap-vcpkg.sh"
        if not dry_run:
            bootstrap.chmod(bootstrap.stat().st_mode | 0o111)
        return drain([str(bootstrap), "-disableMetrics"], dry_run)

    def dependency_manager(self, managers: Sequence[M]) -> M | None:
        """Return the first available manager of ``K_LINUX_MANAGERS``, taken in that order."""
        for name in K_LINUX_MANAGERS:
            for manager in managers:
                if manager.name == name and manager.available():
                    return manager
        return None

    def acpp_skip_notes(self, llvm_version: str) -> list[str]:
        """Return the line naming the LLVM dev packages to install."""
        return ["To enable acpp on Linux, install the LLVM dev packages, e.g. "
                "(Debian/Ubuntu): clang-17 llvm-17-dev libclang-17-dev "
                "libboost-context-dev libboost-fiber-dev, then re-run "
                "`sr setup --profile normal`."]

    def acpp_configure_args(self, vcpkg_toolchain_file: Path) -> list[str]:
        """Return no arguments: the distro supplies the LLVM the build finds."""
        return []

    def prepare_acpp_environment(self, env: MutableMapping[str, str],
                                 find_rc_dir: Callable[[], str]) -> None:
        """Leave *env* as it is: no resource compiler is needed."""
