# cuda.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The CUDA backend: the toolkit release chosen for this machine's cards, located and installed.

No CUDA version is written here. The release comes from the hardware: the newest one NVIDIA
publishes that the driver runs and whose compiler builds for every card. The reasoning is in
docs/design/CUDA_TOOLKIT_SELECTION.md.
"""

from __future__ import annotations

import glob
import os
import pathlib
import platform as host_platform
import shutil
import typing

from .._output import console
from ..user_environment import UserEnvironment, read_user_variable, write_user_variable
from .backend import GpuBackendSpec, PlatformLocator, ToolkitInstall
from .cuda_choice import CudaChoice
from .cuda_choice_file import CudaChoiceFile
from .cuda_hardware import NvidiaHardware, query_hardware
from .cuda_redist import RedistError, RedistIndex
from .cuda_release import Version, format_version, parse_version
from .cuda_selection import select_release
from .cuda_toolkit_installer import (
    RedistToolkitInstaller,
    ToolkitInstallError,
    nvcc_in,
    toolkits_dir,
)

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig

#: Names a release, or a release prefix such as ``12.6``, to install instead of choosing one.
K_RELEASE_OVERRIDE = "SUSHISYSTEMS_CUDA_RELEASE"

#: The variable every CUDA consumer, SushiRuntime's locator included, reads the root from.
K_CUDA_PATH = "CUDA_PATH"

# Neither the apt CUDA toolkit nor a manual install adds itself to PATH.
K_NVCC_GLOBS_LINUX = (
    "/usr/local/cuda/bin/nvcc",
    "/usr/local/cuda-*/bin/nvcc",
)


def redist_platform_key() -> str:
    """Return the redistributable platform key of this machine, such as ``windows-x86_64``."""
    if os.name == "nt":
        return "windows-x86_64"
    machine = host_platform.machine().lower()
    return "linux-sbsa" if machine in ("aarch64", "arm64") else "linux-x86_64"


@typing.final
class CudaLocator:
    """Finds the CUDA toolkit in use and installs the release this machine's hardware needs.

    Args:
        hardware: Returns the cards and the driver's CUDA ceiling, or None without a driver.
        index: NVIDIA's redistributable index.
        installer: Downloads and unpacks releases.
        choices: The record of the last choice; ``<home>/cuda/choice.json`` when None.
        environment: The user's persistent variables; the platform's default when None.
    """

    def __init__(self,
                 hardware: typing.Callable[[], NvidiaHardware | None] = query_hardware,
                 index: RedistIndex | None = None,
                 installer: RedistToolkitInstaller | None = None,
                 choices: CudaChoiceFile | None = None,
                 environment: UserEnvironment | None = None) -> None:
        """Store the collaborators, defaulting to the real ones."""
        self._hardware = hardware
        self._index = index or RedistIndex()
        self._installer = installer or RedistToolkitInstaller()
        self._choices = choices
        self._environment = environment

    def locate(self, cfg: "ProvisionConfig") -> ToolkitInstall | None:
        """Return the toolkit named by CUDA_PATH, in this process or the user's variables,
        else an nvcc on PATH or under a well-known Linux prefix."""
        for raw in (os.environ.get(K_CUDA_PATH, ""),
                    read_user_variable(K_CUDA_PATH, self._environment) or ""):
            found = _toolkit_at(raw)
            if found is not None:
                return found
        nvcc = shutil.which("nvcc") or ("" if os.name == "nt" else _glob_nvcc())
        if not nvcc:
            return None
        return ToolkitInstall(root=pathlib.Path(nvcc).resolve().parent.parent, version=None)

    def provision(self, cfg: "ProvisionConfig", dry_run: bool) -> bool:
        """Install the release this machine needs and point CUDA_PATH at it.

        Always returns True: without a driver, a network or a fitting release the CPU path
        still builds, and the reason is reported.
        """
        hardware = self._hardware()
        if hardware is None:
            console.warn("nvidia-smi did not report a card; the CUDA toolkit is not installed "
                         "and the build uses the CPU path.")
            return True
        major, minor = hardware.driver_cuda
        console.info(f"NVIDIA cards {_architectures_text(hardware)}; the driver runs CUDA up "
                     f"to {major}.{minor}.")
        if dry_run:
            console.info("(dry-run) would choose the CUDA release for this hardware and "
                         f"install it under {self._installer.root_of('<release>').parent}.")
            return True
        try:
            root = self._provide(hardware, redist_platform_key())
        except (RedistError, ToolkitInstallError) as error:
            self._installer.discard_downloads()
            self._report_failure(cfg, str(error))
            return True
        if root is None:
            return True
        os.environ[K_CUDA_PATH] = str(root)
        write_user_variable(K_CUDA_PATH, str(root), self._environment)
        console.success(f"CUDA toolkit at {root}; {K_CUDA_PATH} points to it.")
        return True

    def _provide(self, hardware: NvidiaHardware, key: str) -> pathlib.Path | None:
        """Return the root of the release to use, installing it when needed."""
        override = os.environ.get(K_RELEASE_OVERRIDE, "").strip()
        if override:
            return self._install(self._resolve_override(override), key)
        choices = self._choices or CudaChoiceFile(toolkits_dir() / "choice.json")
        recorded = choices.read()
        if (recorded is not None and recorded.fingerprint == hardware.fingerprint()
                and recorded.platform == key and self._installer.is_installed(recorded.release)):
            console.info(f"CUDA {recorded.release} was chosen for this hardware before.")
            return self._installer.root_of(recorded.release)
        chosen = select_release(hardware, self._index.versions(),
                                lambda version: self._architectures(version, key))
        if chosen is None:
            self._installer.discard_downloads()
            console.warn(f"No published CUDA release that the driver runs builds for "
                         f"{_architectures_text(hardware)}; update the NVIDIA driver, or set "
                         f"{K_RELEASE_OVERRIDE}. The build uses the CPU path.")
            return None
        console.info(f"CUDA {format_version(chosen)} is the newest release that builds for "
                     "every card here.")
        root = self._install(chosen, key)
        choices.write(CudaChoice(hardware.fingerprint(), key, format_version(chosen)))
        return root

    def _install(self, version: Version, key: str) -> pathlib.Path:
        """Install *version* unless it is already in place, and return its root."""
        label = format_version(version)
        if self._installer.is_installed(label):
            return self._installer.root_of(label)
        console.info(f"Installing the CUDA {label} compiler, runtime and libraries under "
                     f"{self._installer.root_of(label)}.")
        return self._installer.install(self._index.release(version, key))

    def _architectures(self, version: Version, key: str) -> frozenset[str]:
        """Return what *version*'s compiler builds for; an unreadable one builds for nothing."""
        console.info(f"Asking the CUDA {format_version(version)} compiler which cards it "
                     "builds for ...")
        try:
            return self._installer.probe_architectures(self._index.release(version, key))
        except (RedistError, ToolkitInstallError) as error:
            console.warn(f"CUDA {format_version(version)} skipped: {error}")
            return frozenset()

    def _resolve_override(self, text: str) -> Version:
        """Return the newest published release that *text* names or prefixes.

        Raises:
            RedistError: *text* is not a version, or no published release matches it.
        """
        try:
            wanted = parse_version(text)
        except ValueError as error:
            raise RedistError(f"{K_RELEASE_OVERRIDE}={text} is not a CUDA version") from error
        for version in self._index.versions():
            if version[:len(wanted)] == wanted:
                console.info(f"{K_RELEASE_OVERRIDE} asks for CUDA {format_version(version)}.")
                return version
        raise RedistError(f"NVIDIA publishes no CUDA release matching {text}")

    def _report_failure(self, cfg: "ProvisionConfig", reason: str) -> None:
        """Say why no release was installed and what the build uses instead."""
        existing = self.locate(cfg)
        fallback = (f"the toolkit at {existing.root} stays in use" if existing is not None
                    else "the build uses the CPU path")
        console.warn(f"CUDA toolkit not installed: {reason}; {fallback}.")


def _architectures_text(hardware: NvidiaHardware) -> str:
    """Return the cards as ``sm_61, sm_89``."""
    return ", ".join(f"sm_{arch}" for arch in hardware.architectures)


def _toolkit_at(raw: str) -> ToolkitInstall | None:
    """Return the toolkit rooted at *raw* when its nvcc exists, else None."""
    if not raw:
        return None
    root = pathlib.Path(os.path.normpath(raw))
    if not nvcc_in(root).is_file():
        return None
    return ToolkitInstall(root=root, version=None)


def _glob_nvcc() -> str:
    """Return the newest nvcc found under the well-known Linux install globs."""
    for pattern in K_NVCC_GLOBS_LINUX:
        hits = sorted(glob.glob(pattern))
        if hits:
            return hits[-1]
    return ""


def _adapter_definitions(install: ToolkitInstall) -> dict[str, str]:
    """Name the CUDA toolkit root to the Unified Runtime CUDA adapter build."""
    return {"CUDAToolkit_ROOT": str(install.root)}


CUDA = GpuBackendSpec(
    vendor="cuda",
    probe_vendor="nvidia",
    locator=PlatformLocator("CUDA", dict.fromkeys(("linux", "windows"), CudaLocator())),
    adapter_option="UR_BUILD_ADAPTER_CUDA",
    adapter_definitions=_adapter_definitions,
    adapter_target="ur_adapter_cuda",
    adapter_binaries=("ur_adapter_cuda", "umf"),
)
