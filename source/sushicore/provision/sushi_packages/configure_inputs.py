# configure_inputs.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Hashes what a library's configure step reads besides its sources."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Callable

from .package_error import PackageError

#: The files, relative to the checkout, whose content is a configure input.
K_FILES = ("cli/config.local.toml", "vcpkg.json", "vcpkg-configuration.json")

#: Returns the version text of CMake, such as ``3.28.1``.
CMakeVersion = Callable[[], str]

#: Returns the commit of the vcpkg tree at a path, or '' when it has none.
VcpkgHead = Callable[[Path], str]


def probe_cmake_version(cmake: str = "cmake") -> str:
    """Return the version of *cmake* from ``cmake --version``.

    Raises:
        PackageError: CMake does not run or prints no version.
    """
    try:
        result = subprocess.run([cmake, "--version"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        raise PackageError(f"cannot run {cmake} --version: {exc}") from exc
    found = re.search(r"(\d+\.\d+(?:\.\d+)?)", result.stdout)
    if result.returncode != 0 or not found:
        raise PackageError(f"{cmake} --version printed no version.")
    return found.group(1)


def probe_vcpkg_head(vcpkg_root: Path) -> str:
    """Return the HEAD commit of the vcpkg tree at *vcpkg_root*, or '' when git cannot say."""
    try:
        result = subprocess.run(["git", "-C", str(vcpkg_root), "rev-parse", "HEAD"],
                                capture_output=True, text=True)
    except OSError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


class ConfigureInputs:
    """Reads the configure inputs of a library into one hash."""

    def __init__(self, cmake_version: CMakeVersion = probe_cmake_version,
                 vcpkg_head: VcpkgHead = probe_vcpkg_head) -> None:
        """Bind the reader to the two probes.

        Args:
            cmake_version: Returns the CMake version text; replaced in tests.
            vcpkg_head: Returns the commit of a vcpkg tree; replaced in tests.
        """
        self._cmake_version = cmake_version
        self._vcpkg_head = vcpkg_head

    def read(self, checkout: Path, vcpkg_root: Path | None, triplet: str) -> str:
        """Return the SHA-256, as hex, of the inputs of the library at *checkout*.

        The inputs are the content of :data:`K_FILES` (a missing file counts as absent), the
        HEAD of the vcpkg tree, the triplet, and the CMake major and minor version.
        """
        parts = {
            "files": {name: self._file_hash(checkout / name) for name in K_FILES},
            "vcpkg": self._vcpkg_head(vcpkg_root) if vcpkg_root is not None else "",
            "triplet": triplet,
            "cmake": ".".join(self._cmake_version().split(".")[:2]),
        }
        text = json.dumps(parts, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _file_hash(path: Path) -> str:
        """Return the SHA-256 of *path*, or '' when there is no such file."""
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except FileNotFoundError:
            return ""
        except OSError as exc:
            raise PackageError(f"cannot read {path}: {exc}") from exc
