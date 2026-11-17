# base.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The contract for what differs between the operating systems provision runs on."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from sushicore.proc import CommandRunner


class IHost(ABC):
    """Does the operating-system work whose form differs between Windows and POSIX hosts."""

    @abstractmethod
    def make_dir_link(self, link: Path, target: Path) -> None:
        """Create *link* as a directory link to *target*."""

    @abstractmethod
    def remove_dir_link(self, path: Path) -> None:
        """Remove the directory link *path* without touching what it points to."""

    @abstractmethod
    def replace_dir_link(self, link: Path, target: Path) -> None:
        """Make *link* name *target*, replacing a link already at *link*."""

    @abstractmethod
    def is_junction(self, path: Path) -> bool:
        """Report whether *path* is a Windows junction; False on a host without junctions."""

    @abstractmethod
    def try_lock(self, fd: int) -> bool:
        """Attempt a non-blocking exclusive OS lock on *fd*; return whether it succeeded."""

    @abstractmethod
    def unlock(self, fd: int) -> None:
        """Release the OS lock acquired on *fd* with :meth:`try_lock`."""

    @abstractmethod
    def registry_paths(self) -> list[str] | None:
        """Return the ``Path`` values the OS keeps outside the process, or None when it keeps none.

        Raises:
            OSError: The store may not be read.
        """

    @abstractmethod
    def display_adapters(self, runner: CommandRunner) -> str:
        """Return the lower-case display adapters the OS reports, or ''; *runner* runs the query."""

    @abstractmethod
    def long_path(self, path: Path) -> Path:
        """Return *path* in the form that lifts the host's path-length limit."""

    @property
    @abstractmethod
    def nvcc_name(self) -> str:
        """The file name of the CUDA compiler."""

    @property
    @abstractmethod
    def cuda_platform_key(self) -> str:
        """This machine's key in NVIDIA's redistributable index, such as ``windows-x86_64``."""

    @property
    @abstractmethod
    def searches_system_prefixes(self) -> bool:
        """Whether toolkits may sit under a well-known system prefix such as ``/opt/rocm``."""

    @property
    @abstractmethod
    def hosts_visual_studio(self) -> bool:
        """Whether Visual Studio can be installed on this host."""

    @property
    @abstractmethod
    def keeps_environment_in_registry(self) -> bool:
        """Whether the user's variables live in the registry, not in a shell profile."""
