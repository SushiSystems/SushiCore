# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The CUDA backend: NVIDIA's toolkit, located and provisioned per platform."""

from __future__ import annotations

import glob
import os
import pathlib
import shutil
import subprocess
import typing

from .. import probe
from .._output import console
from ..system import is_root, os_release, sudo_bash
from .backend import GpuBackendSpec, PlatformLocator, ToolkitInstall
from .windows_installer import (
    ELEVATION_DECLINED,
    ElevatedResult,
    InstallerDownload,
    WindowsInstallerTools,
    adopt_machine_variable,
    prepend_machine_path,
)

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig

# Neither the apt CUDA toolkit nor a manual install adds itself to PATH, so a
# fresh machine needs these well-known roots checked directly.
_NVCC_GLOBS_LINUX = [
    "/usr/local/cuda/bin/nvcc",
    "/usr/local/cuda-*/bin/nvcc",
]

# Ubuntu tag ceiling for NVIDIA's CUDA 12.6 apt repo.
_CUDA126_MAX_UBUNTU_TAG = "ubuntu2404"

# NVIDIA's CUDA 12.6.3 network installer and the MD5 NVIDIA publishes for it.
_WINDOWS_INSTALLER = InstallerDownload(
    url=("https://developer.download.nvidia.com/compute/cuda/12.6.3/"
         "network_installers/cuda_12.6.3_windows_network.exe"),
    file_name="cuda_12.6.3_windows_network.exe",
    md5="48d5d66c3550b7744715c638dac4f522",
)

# Silent mode (-s) with the subpackages the adapter build needs; -n forbids a reboot.
_WINDOWS_INSTALLER_ARGS = (
    "-s", "nvcc_12.6", "cudart_12.6", "nvml_dev_12.6", "-n",
)

_MANUAL_HINT = ("Install CUDA Toolkit 12.6 from "
                "https://developer.nvidia.com/cuda-12-6-3-download-archive; the build "
                "otherwise uses the CPU path.")


def _apt_distro_tag() -> str:
    """Return the NVIDIA/ROCm-style distro tag for repo URLs, or '' if unknown."""
    rel = os_release()
    idv = rel.get("ID", "").lower()
    ver = rel.get("VERSION_ID", "").replace(".", "")
    if idv in ("ubuntu", "debian") and ver:
        return f"{idv}{ver}"
    return ""


def _cuda_repo_tag() -> str:
    """Return the distro tag for NVIDIA's CUDA apt repo, clamped to one that ships 12.6."""
    tag = _apt_distro_tag()
    if not tag:
        return ""
    if tag.startswith("ubuntu"):
        try:
            ver = int(tag[len("ubuntu"):])
        except ValueError:
            return tag
        if ver > int(_CUDA126_MAX_UBUNTU_TAG[len("ubuntu"):]):
            console.info(f"NVIDIA has no CUDA 12.6 repo for {tag}; using "
                         f"{_CUDA126_MAX_UBUNTU_TAG} (Pascal-capable, runs on newer Ubuntu).")
            return _CUDA126_MAX_UBUNTU_TAG
    return tag


class LinuxCudaLocator:
    """Finds and installs the CUDA toolkit from NVIDIA's official apt repo."""

    def locate(self, cfg: "ProvisionConfig") -> ToolkitInstall | None:
        """Return the CUDA toolkit root found via PATH or a well-known glob."""
        nvcc = shutil.which("nvcc") or self._glob_nvcc()
        if not nvcc:
            return None
        root = pathlib.Path(nvcc).resolve().parent.parent
        return ToolkitInstall(root=root, version=None)

    def _glob_nvcc(self) -> str:
        """Return the newest nvcc found under the well-known CUDA install globs."""
        for pattern in _NVCC_GLOBS_LINUX:
            hits = sorted(glob.glob(pattern))
            if hits:
                return hits[-1]
        return ""

    def provision(self, cfg: "ProvisionConfig", dry_run: bool) -> bool:
        """Install the pinned NVIDIA CUDA toolkit from NVIDIA's official apt repo."""
        if probe.binary_works("nvcc"):
            console.info("CUDA toolkit already present (nvcc found).")
            return True
        tag = _cuda_repo_tag()
        if not tag:
            console.warn("Unrecognised distro for the NVIDIA CUDA repo; install the "
                         "CUDA 12.x toolkit manually "
                         "(https://developer.nvidia.com/cuda-downloads).")
            return False
        sudo = "" if is_root() else "sudo "
        keyring_url = (f"https://developer.download.nvidia.com/compute/cuda/repos/"
                       f"{tag}/x86_64/cuda-keyring_1.1-1_all.deb")
        steps = (
            f"tmp=$(mktemp -d) && cd \"$tmp\" && "
            f"curl -fsSLO {keyring_url} && "
            f"{sudo}dpkg -i cuda-keyring_1.1-1_all.deb && "
            f"{sudo}apt-get update && "
            f"{sudo}apt-get install -y cuda-toolkit-12-6"
        )
        if not sudo_bash(steps, dry_run):
            console.warn("CUDA toolkit install failed. Install CUDA 12.x manually "
                         "(https://developer.nvidia.com/cuda-downloads); the build will "
                         "otherwise fall back to the CPU/OpenCL path.")
            return False
        return True


class WindowsCudaLocator:
    """Finds the CUDA toolkit through CUDA_PATH and installs it with NVIDIA's network installer.

    :param tools: The download, elevation and machine-environment helpers.
    """

    def __init__(self, tools: WindowsInstallerTools | None = None) -> None:
        """Store the installer helpers, defaulting to the real ones."""
        self._tools = tools or WindowsInstallerTools()

    def locate(self, cfg: "ProvisionConfig") -> ToolkitInstall | None:
        """Return the toolkit named by the process CUDA_PATH, else by the machine CUDA_PATH.

        A valid machine value is copied into this process, so a build started from
        it inherits the toolkit even when the terminal predates the CUDA install.
        """
        found = _toolkit_at(os.environ.get("CUDA_PATH", ""))
        if found is not None:
            return found
        machine = self._tools.environment.read("CUDA_PATH") or ""
        found = _toolkit_at(machine)
        if found is not None:
            os.environ["CUDA_PATH"] = machine
        return found

    def provision(self, cfg: "ProvisionConfig", dry_run: bool) -> bool:
        """Report an existing toolkit, or download and silently install the pinned one.

        Always returns True: a failed download, a declined UAC prompt or a failed
        install leaves the CPU path working.
        """
        found = self.locate(cfg)
        if found is not None:
            console.info(f"CUDA toolkit already present at {found.root}.")
            return True
        dest_dir = self._tools.dest_dir()
        exe = dest_dir / _WINDOWS_INSTALLER.file_name
        command = self._tools.runner.command(exe, _WINDOWS_INSTALLER_ARGS)
        if dry_run:
            console.info(f"(dry-run) would download {_WINDOWS_INSTALLER.url} to {exe}")
            console.command(subprocess.list2cmdline(command))
            return True
        downloaded = self._tools.downloader.fetch(_WINDOWS_INSTALLER, dest_dir)
        if downloaded is None:
            console.warn(f"CUDA toolkit not installed: {_WINDOWS_INSTALLER.file_name} "
                         "could not be downloaded and verified. " + _MANUAL_HINT)
            return True
        console.info("Installing the CUDA 12.6 compiler, runtime and libraries. Windows "
                     "will ask once for administrator rights.")
        console.command(subprocess.list2cmdline(command))
        result = self._tools.runner.run(downloaded, _WINDOWS_INSTALLER_ARGS)
        self._refresh_environment()
        installed = self.locate(cfg)
        if installed is None:
            console.warn(f"CUDA toolkit not installed: {_failure_reason(result)}. "
                         + _MANUAL_HINT)
            return True
        suffix = f" (installer exit code {result.code})" if result.code else ""
        console.success(f"CUDA toolkit installed at {installed.root}{suffix}.")
        _delete_quietly(downloaded)
        return True

    def _refresh_environment(self) -> None:
        """Copy the machine CUDA_PATH and the new machine PATH entries into this process."""
        adopt_machine_variable(self._tools.environment, "CUDA_PATH")
        prepend_machine_path(self._tools.environment)


def _toolkit_at(raw: str) -> ToolkitInstall | None:
    """Return the toolkit rooted at *raw* when its bin/nvcc.exe exists, else None."""
    if not raw:
        return None
    root = pathlib.Path(os.path.normpath(raw))
    if not (root / "bin" / "nvcc.exe").is_file():
        return None
    return ToolkitInstall(root=root, version=None)


def _failure_reason(result: ElevatedResult) -> str:
    """Describe why an elevated installer run left no toolkit behind."""
    if result.code == ELEVATION_DECLINED:
        return "the administrator prompt was declined"
    if result.message:
        return f"the installer could not start (code {result.code}): {result.message}"
    return f"the installer exited with code {result.code}"


def _delete_quietly(path: pathlib.Path) -> None:
    """Delete *path*, ignoring a file that is locked or already gone."""
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _adapter_definitions(install: ToolkitInstall) -> dict[str, str]:
    """Name the CUDA toolkit root to the Unified Runtime CUDA adapter build."""
    return {"CUDAToolkit_ROOT": str(install.root)}


CUDA = GpuBackendSpec(
    vendor="cuda",
    probe_vendor="nvidia",
    locator=PlatformLocator("CUDA", {
        "linux": LinuxCudaLocator(),
        "windows": WindowsCudaLocator(),
    }),
    adapter_option="UR_BUILD_ADAPTER_CUDA",
    adapter_definitions=_adapter_definitions,
    adapter_target="ur_adapter_cuda",
    adapter_binaries=("ur_adapter_cuda", "umf"),
)
