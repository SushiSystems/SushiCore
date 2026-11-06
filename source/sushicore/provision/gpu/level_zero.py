# level_zero.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The Level Zero backend: Intel's GPU compute stack, located on Linux."""

from __future__ import annotations

import ctypes.util
import pathlib
import typing

from .._output import console
from ..system import ensure_intel_oneapi_repo, is_root, sudo_bash
from .backend import GpuBackendSpec, PlatformLocator, ToolkitInstall

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig

# Fallback directories checked when ctypes.util.find_library finds nothing.
_ZE_LOADER_LIB_DIRS = (
    "/usr/lib/x86_64-linux-gnu",
    "/usr/lib64",
    "/usr/lib",
)
_ZE_LOADER_GLOB = "libze_loader.so*"


def _find_ze_loader(find_library: typing.Callable[[str], str | None],
                    lib_dirs: typing.Iterable[str]) -> pathlib.Path | None:
    """Return the directory holding libze_loader, or None when it is absent.

    Args:
        find_library: Answers the path of a library by name, as :func:`ctypes.util.find_library`.
        lib_dirs: The directories searched when *find_library* finds nothing.
    """
    found = find_library("ze_loader")
    if found:
        path = pathlib.PurePosixPath(found)
        return pathlib.Path(str(path.parent)) if path.is_absolute() else pathlib.Path("/usr/lib")
    for directory in lib_dirs:
        if next(pathlib.Path(directory).glob(_ZE_LOADER_GLOB), None) is not None:
            return pathlib.Path(directory)
    return None


class LinuxLevelZeroLocator:
    """Finds and installs the Intel GPU compute stack (Level Zero + OpenCL).

    Args:
        find_library: Answers the path of a library by name; :func:`ctypes.util.find_library`
            when None.
        lib_dirs: The directories searched when the library lookup finds nothing; the
            well-known Linux library directories when None.
        ensure_repo: Sets up Intel's package repository and returns whether it is ready;
            :func:`ensure_intel_oneapi_repo` when None.
        is_superuser: Reports whether the process is root; :func:`is_root` when None.
        run_steps: Runs one shell line, with sudo where it says so, and returns whether it
            succeeded; :func:`sudo_bash` when None.
    """

    def __init__(self, *, find_library: typing.Callable[[str], str | None] | None = None,
                 lib_dirs: typing.Iterable[str] | None = None,
                 ensure_repo: typing.Callable[[bool], bool] | None = None,
                 is_superuser: typing.Callable[[], bool] | None = None,
                 run_steps: typing.Callable[[str, bool], bool] | None = None) -> None:
        """Store the collaborators, defaulting to the real ones."""
        self._find_library = find_library or ctypes.util.find_library
        self._lib_dirs = tuple(_ZE_LOADER_LIB_DIRS if lib_dirs is None else lib_dirs)
        self._ensure_repo = ensure_repo or ensure_intel_oneapi_repo
        self._is_superuser = is_superuser or is_root
        self._run_steps = run_steps or sudo_bash

    def locate(self, cfg: "ProvisionConfig") -> ToolkitInstall | None:
        """Return the directory holding the Level Zero loader, or None."""
        directory = _find_ze_loader(self._find_library, self._lib_dirs)
        if directory is None:
            return None
        return ToolkitInstall(root=directory, version=None)

    def provision(self, cfg: "ProvisionConfig", dry_run: bool) -> bool:
        """Install the Intel GPU compute stack (Level Zero + OpenCL) for Intel GPUs."""
        if not self._ensure_repo(dry_run):
            return False
        sudo = "" if self._is_superuser() else "sudo "
        steps = (
            f"{sudo}apt-get update && "
            f"{sudo}apt-get install -y level-zero intel-oneapi-runtime-opencl "
            f"intel-oneapi-runtime-libs"
        )
        if not self._run_steps(steps, dry_run):
            console.warn("Intel GPU runtime install failed; the build will fall back "
                         "to the CPU/OpenCL path.")
            return False
        return True


LEVEL_ZERO = GpuBackendSpec(
    vendor="level_zero",
    probe_vendor="intel",
    locator=PlatformLocator("Level Zero", {
        "linux": LinuxLevelZeroLocator(),
    }),
    adapter_option="UR_BUILD_ADAPTER_L0",
    adapter_definitions=lambda install: {},
    adapter_target="ur_adapter_level_zero",
    adapter_binaries=("ur_adapter_level_zero", "umf"),
)
