# windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The probe plan of the Windows target."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable, final

from .. import home
from ..config import ProvisionConfig
from ..probe import (
    K_ICX_GLOBS,
    K_RC_GLOBS,
    binary_works,
    discover_installed_toolchains,
    find_vcvars,
    first_existing,
    first_glob_match,
)
from ..probe_plan import PROBE_PLANS, IProbePlan
from ..target import K_WINDOWS

#: Visual Studio 2022 script locations tried before the vswhere and disk-scan fallbacks.
K_VS_VCVARS_GLOBS = [
    r"C:/Program Files/Microsoft Visual Studio/2022/*/VC/Auxiliary/Build/vcvars64.bat",
    r"C:/Program Files (x86)/Microsoft Visual Studio/2022/*/VC/Auxiliary/Build/vcvars64.bat",
]

#: oneAPI install roots tried when the config names none.
K_ONEAPI_ROOTS = [
    r"C:/Program Files (x86)/Intel/oneAPI",
    r"C:/Program Files/Intel/oneAPI",
]


@final
class WindowsProbePlan(IProbePlan):
    """Finds oneAPI ``icx-cl`` and the Windows tool paths in the config, install roots and PATH."""

    def __init__(self, first_glob: Callable[[list[str]], str] | None = None,
                 vcvars_finder: Callable[[], Path | None] | None = None) -> None:
        """Bind the seams that read the machine.

        Args:
            first_glob: Gives the best match among glob patterns, or ''; ``first_glob_match`` when ``None``.
            vcvars_finder: Gives the Visual Studio script the scan finds; ``find_vcvars`` when ``None``.
        """
        self._first_glob = first_glob or first_glob_match
        self._vcvars_finder = vcvars_finder or find_vcvars

    def find_sycl_compiler(self, cfg: ProvisionConfig) -> tuple[str | None, str]:
        """Return the working oneAPI ``icx-cl`` from the config, the install roots or PATH."""
        icx = cfg.expand(cfg.icx_compiler) if cfg.icx_compiler else ""
        if icx and Path(icx).is_file() and binary_works(icx):
            return ("icx-cl", icx)
        hit = first_glob_match(K_ICX_GLOBS) or shutil.which("icx-cl") or shutil.which("icx") or ""
        if hit and binary_works(hit):
            return ("icx-cl", hit)
        return (None, "")

    def resolve_local_config(self, cfg: ProvisionConfig) -> dict[str, str]:
        """Probe Windows-specific tool paths for the local config."""
        values: dict[str, str] = {}

        vcvars = cfg.expand(cfg.vs_vcvars) if cfg.vs_vcvars else ""
        if not (vcvars and Path(vcvars).is_file()):
            vcvars = self._first_glob(K_VS_VCVARS_GLOBS) or str(self._vcvars_finder() or "")
        if vcvars:
            values["vs_vcvars"] = vcvars

        oneapi = cfg.expand(cfg.oneapi_root) if cfg.oneapi_root else ""
        if not (oneapi and Path(oneapi).is_dir()):
            oneapi = first_existing(K_ONEAPI_ROOTS)
        if oneapi:
            values["oneapi_root"] = oneapi

        icx = first_glob_match(K_ICX_GLOBS) or shutil.which("icx-cl") or shutil.which("icx") or ""
        if icx:
            values["icx_compiler"] = icx

        # clang++ runs GNU-like, not clang-cl, so vcvars is never sourced for rc.exe.
        rc = shutil.which("rc") or first_glob_match(K_RC_GLOBS)
        if rc:
            values["rc_exe"] = rc

        tools = home.tools_dir()
        portable_bin = tools / "cmake" / "bin"
        ninja = shutil.which("ninja") or first_existing([str(tools / "ninja.exe")])
        if ninja:
            values["ninja_exe"] = ninja

        # cmake/ctest may be off PATH in a non-interactive shell, so known install locations are checked too.
        cmake_candidates = [str(portable_bin / "cmake.exe"),
                            r"C:/Program Files/CMake/bin/cmake.exe",
                            r"C:/Program Files (x86)/CMake/bin/cmake.exe"]
        ctest_candidates = [str(portable_bin / "ctest.exe"),
                            r"C:/Program Files/CMake/bin/ctest.exe",
                            r"C:/Program Files (x86)/CMake/bin/ctest.exe"]
        cmake = shutil.which("cmake") or first_existing(cmake_candidates)
        if cmake:
            values["cmake_exe"] = cmake
        ctest = shutil.which("ctest") or first_existing(ctest_candidates)
        if ctest:
            values["ctest_exe"] = ctest

        pkgconf = shutil.which("pkg-config") or shutil.which("pkgconf")
        vcpkg_root = cfg.expand(cfg.vcpkg_root) if cfg.vcpkg_root else ""
        # Ignore a configured path that points inside a conda/venv tree.
        if vcpkg_root and (".conda" in vcpkg_root or "envs" in vcpkg_root):
            vcpkg_root = ""
        if not (vcpkg_root and Path(vcpkg_root).is_dir()):
            # Default to the first dependency root holding a vcpkg tree, else the current root's.
            vcpkg_root = str(home.found_vcpkg_dir())
        if vcpkg_root:
            values["vcpkg_root"] = vcpkg_root
            # pkgconf shipped by vcpkg is the one CMakeLists expects.
            triplet = cfg.vcpkg_triplet or "x64-windows"
            vcpkg_pkgconf = Path(vcpkg_root) / "installed" / triplet / "tools" / "pkgconf" / "pkgconf.exe"
            if vcpkg_pkgconf.is_file():
                pkgconf = str(vcpkg_pkgconf)
        if pkgconf:
            values["pkgconf_exe"] = pkgconf

        doxy = shutil.which("doxygen") or first_existing([
            str(tools / "doxygen" / "doxygen.exe"),
            r"C:/Program Files/doxygen/bin/doxygen.exe",
            r"C:/Program Files (x86)/doxygen/bin/doxygen.exe",
        ])
        if doxy:
            values["doxygen_exe"] = doxy

        discover_installed_toolchains(cfg, values)
        return values


PROBE_PLANS.register(K_WINDOWS, WindowsProbePlan())
