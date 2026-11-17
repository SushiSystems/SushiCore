# base.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The contract for what differs between the platforms a provision run targets."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, MutableMapping, Protocol, Sequence, TypeVar

from ..config import ProvisionConfig

#: The ``platform`` value of a run that targets Windows.
K_WINDOWS = "windows"

#: The ``platform`` value of a run that targets Linux.
K_LINUX = "linux"


class INamedManager(Protocol):
    """The two things a target asks of a package manager when it picks one."""

    name: str

    def available(self) -> bool:
        """Report whether the manager can run on this machine."""


M = TypeVar("M", bound=INamedManager)


class ITarget(ABC):
    """Answers what a run's target platform decides: names, paths, commands and messages."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the platform name, the ``platform`` value of the config it was chosen from."""

    @property
    @abstractmethod
    def clang_executable(self) -> str:
        """Return the file name of the SYCL clang++ driver."""

    @property
    @abstractmethod
    def nvcc_executable(self) -> str:
        """Return the file name of the CUDA compiler driver."""

    @property
    @abstractmethod
    def python_executable(self) -> str:
        """Return the name the Python interpreter is looked up by on PATH."""

    @property
    @abstractmethod
    def vcpkg_executable(self) -> str:
        """Return the file name of the vcpkg executable."""

    @property
    @abstractmethod
    def vcpkg_triplet(self) -> str:
        """Return the vcpkg triplet installed for when the config names none."""

    @property
    @abstractmethod
    def acpp_launcher(self) -> str:
        """Return the file name of the AdaptiveCpp launcher."""

    @property
    @abstractmethod
    def intel_llvm_asset(self) -> str:
        """Return the file name of the intel/llvm bundle release asset."""

    @property
    @abstractmethod
    def searches_system_prefixes(self) -> bool:
        """Report whether toolchains are also looked for under well-known system prefixes."""

    @property
    @abstractmethod
    def system_prerequisites_note(self) -> str:
        """Return the sentence naming what stays installed outside the dependency root."""

    @property
    @abstractmethod
    def no_compiler_detail(self) -> str:
        """Return the failure detail of a compiler check that found no compiler."""

    @property
    @abstractmethod
    def adapter_install_subdir(self) -> str:
        """Return the toolchain subdirectory a Unified Runtime adapter binary installs into."""

    @abstractmethod
    def adapter_binary_patterns(self, base_name: str) -> list[str]:
        """Return the glob patterns of the file *base_name* maps to."""

    @abstractmethod
    def adapter_compiler_args(self, toolchain_root: Path) -> list[str]:
        """Return the cmake arguments that name the adapter build's compiler and linker."""

    @abstractmethod
    def adapter_build_environment(self, cfg: ProvisionConfig, console: Any) -> dict[str, str]:
        """Return the environment of the adapter build's subprocesses, with *console* for notes."""

    @abstractmethod
    def work_root_fits(self, work_root: Path, warn: Callable[[str], None]) -> bool:
        """Report whether *work_root* is short enough to build in; *warn* names a refusal."""

    @abstractmethod
    def host_compilers(self, cfg: ProvisionConfig) -> list[tuple[str, str]]:
        """Return the ``(label, detail)`` of each compiler the platform adds to the PATH ones."""

    @abstractmethod
    def vcpkg_fallback_ports(self, apt_packages: list[str], vcpkg_ports: list[str]) -> list[str]:
        """Return the vcpkg ports to install for a dependency with these distro packages."""

    @abstractmethod
    def bootstrap_vcpkg(self, root: Path, drain: Callable[[list[str], bool], int],
                        dry_run: bool) -> int:
        """Run the vcpkg bootstrap script under *root* through *drain* and return its exit code."""

    @abstractmethod
    def dependency_manager(self, managers: Sequence[M]) -> M | None:
        """Return the manager that knows whether a manifest dependency is installed, or None."""

    @abstractmethod
    def acpp_skip_notes(self, llvm_version: str) -> list[str]:
        """Return the lines explaining a skipped acpp build; *llvm_version* names the Windows LLVM."""

    @abstractmethod
    def acpp_configure_args(self, vcpkg_toolchain_file: Path) -> list[str]:
        """Return the cmake arguments that wire the vcpkg toolchain file into the acpp build."""

    @abstractmethod
    def prepare_acpp_environment(self, env: MutableMapping[str, str],
                                 find_rc_dir: Callable[[], str]) -> None:
        """Add to *env* what the acpp build needs on PATH; *find_rc_dir* finds the SDK's rc.exe."""
