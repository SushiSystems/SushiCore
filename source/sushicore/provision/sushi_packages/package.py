# package.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""One complete package in the store, and what a consumer reads from its install tree."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from .package_error import PackageError

#: The folder of a package that holds the install prefix.
K_PREFIX = "prefix"

#: The platform string that selects ``bin`` as the run-time folder.
K_WINDOWS = "windows"


@dataclass(frozen=True, slots=True)
class Package:
    """One complete package: its library, digest, folder and stamp."""

    name: str
    digest: str
    root: Path
    stamp: dict[str, Any]

    @property
    def prefix(self) -> Path:
        """Return the install prefix inside the package folder."""
        return self.root / K_PREFIX

    @property
    def toolchain(self) -> str:
        """Return the toolchain identity the stamp records."""
        return str(self.stamp.get("parts", {}).get("toolchain", ""))

    @property
    def build_type(self) -> str:
        """Return the build type the stamp records."""
        return str(self.stamp.get("parts", {}).get("build_type", ""))

    def below(self) -> list[tuple[str, str]]:
        """Return the ``(name, digest)`` of the packages this one was built against."""
        return [(str(name), str(digest))
                for name, digest in self.stamp.get("parts", {}).get("below", [])]

    def config_folder(self) -> Path:
        """Return the folder holding this library's CMake config file.

        The folder is the one named after the library, case apart, under a ``cmake`` folder of
        the prefix, such as ``lib/cmake/SushiBLAS``. Its name is the package's own spelling, which
        is the name of the ``<Package>_DIR`` variable.

        Raises:
            PackageError: The prefix holds no config file for the library.
        """
        for folder in _cmake_folders(self.prefix):
            if folder.name.lower() == self.name and any(
                    path.name.endswith(("Config.cmake", "-config.cmake"))
                    for path in folder.glob("*.cmake")):
                return folder
        raise PackageError(
            f"{self.prefix} holds no CMake config folder named {self.name}; the library's "
            "`package` command did not install its package files.")

    def run_dirs(self, platform: str) -> list[Path]:
        """Return the existing folders that hold the package's shared libraries.

        Args:
            platform: ``"windows"`` selects ``bin``; anything else selects ``lib`` and ``lib64``.
        """
        names = ("bin",) if platform == K_WINDOWS else ("lib", "lib64")
        return [self.prefix / name for name in names if (self.prefix / name).is_dir()]


def _cmake_folders(prefix: Path) -> Iterator[Path]:
    """Yield each folder below a ``cmake`` folder of *prefix*, searching two levels of parents."""
    parents = [prefix]
    if prefix.is_dir():
        for first in prefix.iterdir():
            if first.is_dir():
                parents.append(first)
                parents.extend(second for second in first.iterdir() if second.is_dir())
    for parent in parents:
        cmake = parent / "cmake"
        if cmake.is_dir():
            yield from (path for path in cmake.iterdir() if path.is_dir())
