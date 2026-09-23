# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Fetches, configures and builds one GPU backend's Unified Runtime adapter."""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import subprocess
import typing
from pathlib import Path

from .. import home
from .._output import console
from ..toolchains.stamp import record_toolchain_adapter, toolchain_adapter_commit

if typing.TYPE_CHECKING:
    from .backend import GpuBackendSpec, ToolkitInstall
    from ..config import ProvisionConfig

#: Windows work_root paths beyond this length push fetched object paths past MAX_PATH.
_MAX_WORK_ROOT_LENGTH = 60

#: Commit characters used in directory names under the work root.
_COMMIT_PREFIX_LENGTH = 8

#: Exceptions a failing filesystem or stamp read can raise; caught in :meth:`AdapterBuilder.build`.
_RECOVERABLE_ERRORS = (OSError, ValueError, TypeError, UnicodeError, json.JSONDecodeError)

_UR_REPO_URL = "https://github.com/intel/llvm.git"
_UR_SPARSE_PATH = "/unified-runtime/"


@typing.runtime_checkable
class CommandRunner(typing.Protocol):
    """Runs one command and reports its exit code."""

    def run(self, argv: list[str], cwd: Path | None,
             env: dict[str, str] | None) -> int:
        """Run *argv* in *cwd* under *env* and return its exit code."""
        ...


class SubprocessCommandRunner:
    """Runs a command with :mod:`subprocess`, streaming its output to the console."""

    def run(self, argv: list[str], cwd: Path | None,
             env: dict[str, str] | None) -> int:
        """Run *argv*, printing each output line as it arrives, and return the exit code."""
        console.command(subprocess.list2cmdline(argv))
        process = subprocess.Popen(
            argv, cwd=str(cwd) if cwd else None, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )
        if process.stdout:
            for line in iter(process.stdout.readline, ""):
                console.console.print(line.rstrip("\n"), markup=False, highlight=False)
        process.wait()
        return process.returncode


def _default_work_root() -> Path:
    """Return a short build directory under the shared dependency tree."""
    return home.root() / "ur"


def _default_environment(cfg: "ProvisionConfig") -> dict[str, str]:
    """Return the build environment for the adapter's cmake and ninja subprocesses."""
    if not cfg.is_windows:
        return dict(os.environ)
    from sushicore.build_env import merge_env, snapshot_windows
    snapshot = snapshot_windows(cfg, console)
    if snapshot is None:
        return dict(os.environ)
    return merge_env(os.environ, snapshot)


def _binary_names(base_name: str, is_windows: bool) -> list[str]:
    """Return the platform file names *base_name* maps to."""
    if is_windows:
        return [f"{base_name}.dll"]
    return [f"lib{base_name}.so*"]


def _bin_subdir(is_windows: bool) -> str:
    """Return the toolchain subdirectory an adapter binary installs into."""
    return "bin" if is_windows else "lib"


def _adapters_present(toolchain_root: Path, spec: "GpuBackendSpec",
                      is_windows: bool) -> bool:
    """Report whether every one of *spec*'s adapter binaries already exists."""
    target_dir = toolchain_root / _bin_subdir(is_windows)
    for base_name in spec.adapter_binaries:
        for pattern in _binary_names(base_name, is_windows):
            if not sorted(target_dir.glob(pattern)):
                return False
    return True


@dataclasses.dataclass
class AdapterBuilder:
    """Builds one vendor's Unified Runtime adapter into a toolchain tree.

    :param cfg: Resolved configuration; selects the platform's tools and file
        mapping.
    :param runner: Runs the fetch, configure and build commands.
    :param work_root: Scratch directory for sources and build trees. Defaults
        to a short path under the shared dependency tree.
    :param environment: Returns the environment the build subprocesses run
        under. Defaults to a vcvars64 snapshot on Windows, the current
        environment elsewhere. Called at most once per builder instance.
    """

    cfg: "ProvisionConfig"
    runner: CommandRunner
    work_root: Path = dataclasses.field(default_factory=_default_work_root)
    environment: typing.Callable[["ProvisionConfig"], dict[str, str]] = _default_environment

    _cached_environment: dict[str, str] | None = dataclasses.field(
        default=None, init=False, repr=False)

    def build(self, spec: "GpuBackendSpec", install: "ToolkitInstall",
             toolchain_root: Path, commit: str, dry_run: bool) -> bool:
        """Build *spec*'s adapter at *commit* into *toolchain_root*.

        Skips the build when the toolchain stamp already records this commit
        for this vendor and every mapped binary is present. Any failing step
        is reported and returns False without changing *toolchain_root*.
        """
        try:
            return self._build(spec, install, toolchain_root, commit, dry_run)
        except _RECOVERABLE_ERRORS as exc:
            console.warn(f"{spec.vendor} adapter build failed: {exc}")
            return False

    def _build(self, spec: "GpuBackendSpec", install: "ToolkitInstall",
              toolchain_root: Path, commit: str, dry_run: bool) -> bool:
        """Run the build steps proper, with recoverable errors left to the caller."""
        stamped = toolchain_adapter_commit(toolchain_root, spec.vendor)
        if stamped == commit and _adapters_present(toolchain_root, spec, self.cfg.is_windows):
            console.info(f"{spec.vendor} adapter already built for {commit[:12]}.")
            return True

        if dry_run:
            console.info(f"(dry-run) would build {spec.vendor} adapter at {commit[:12]}")
            return True

        if self.cfg.is_windows:
            work_root_length = len(str(self.work_root.absolute()))
            if work_root_length > _MAX_WORK_ROOT_LENGTH:
                console.warn(
                    f"Adapter build root is {work_root_length} characters, "
                    f"over the {_MAX_WORK_ROOT_LENGTH} limit that avoids "
                    f"Windows' long-path ninja failure: {self.work_root}")
                return False

        env = self._environment()
        short_commit = commit[:_COMMIT_PREFIX_LENGTH]
        src_dir = self.work_root / f"s-{short_commit}"
        build_dir = self.work_root / f"{spec.vendor}-{short_commit}"

        if not self._fetch_sources(src_dir, commit, env):
            return False
        if not self._configure(spec, install, src_dir, build_dir, commit, env):
            return False
        if not self._build_target(spec, build_dir, env):
            return False

        staged = self._stage_binaries(spec, build_dir)
        if staged is None:
            return False

        staging_dir = self.work_root / f"{spec.vendor}-stage"
        try:
            installed = self._install_binaries(toolchain_root, staged)
        finally:
            shutil.rmtree(staging_dir, ignore_errors=True)
        if not installed:
            return False
        record_toolchain_adapter(toolchain_root, spec.vendor, commit)
        console.success(f"{spec.vendor} adapter built for {commit[:12]}.")
        return True

    def _environment(self) -> dict[str, str]:
        """Return the build environment, computed once and reused for this instance."""
        if self._cached_environment is None:
            self._cached_environment = self.environment(self.cfg)
        return self._cached_environment

    def _fetch_sources(self, src_dir: Path, commit: str,
                       env: dict[str, str]) -> bool:
        """Sparse-checkout ``unified-runtime/`` at *commit* into *src_dir*."""
        if (src_dir / "unified-runtime").is_dir():
            return True
        src_dir.mkdir(parents=True, exist_ok=True)
        steps = [
            ["git", "init"],
            ["git", "remote", "add", "origin", _UR_REPO_URL],
            ["git", "sparse-checkout", "set", "--no-cone", _UR_SPARSE_PATH],
            ["git", "fetch", "--depth", "1", "--filter=blob:none", "origin", commit],
            ["git", "checkout", "FETCH_HEAD"],
        ]
        for argv in steps:
            if self._run(argv, src_dir, env) != 0:
                console.warn(f"Fetching unified-runtime sources failed at: {argv}")
                shutil.rmtree(src_dir, ignore_errors=True)
                return False
        return True

    def _configure(self, spec: "GpuBackendSpec", install: "ToolkitInstall",
                   src_dir: Path, build_dir: Path, commit: str,
                   env: dict[str, str]) -> bool:
        """Configure the unified-runtime CMake build for *spec*'s adapter."""
        cmake = self.cfg.expand(self.cfg.cmake_exe) or "cmake"
        argv = [
            cmake,
            "-S", str(src_dir / "unified-runtime"),
            "-B", str(build_dir),
            "-G", "Ninja",
            "-DCMAKE_BUILD_TYPE=Release",
        ]
        if self.cfg.is_windows:
            argv += ["-DCMAKE_C_COMPILER=cl", "-DCMAKE_CXX_COMPILER=cl"]
        ninja = self.cfg.expand(self.cfg.ninja_exe)
        if ninja:
            argv.append(f"-DCMAKE_MAKE_PROGRAM={ninja}")
        argv += [
            f"-D{spec.adapter_option}=ON",
            "-DUR_BUILD_TESTS=OFF",
            "-DUR_BUILD_EXAMPLES=OFF",
            "-DUR_BUILD_TOOLS=OFF",
            "-DUR_ENABLE_SANITIZER=OFF",
            "-DUR_ENABLE_TRACING=OFF",
            f"-DFETCHCONTENT_BASE_DIR={self.work_root / f'd-{commit[:_COMMIT_PREFIX_LENGTH]}'}",
        ]
        for key, value in spec.adapter_definitions(install).items():
            argv.append(f"-D{key}={value}")
        if self._run(argv, None, env) != 0:
            console.warn(f"Configuring the {spec.vendor} adapter build failed.")
            return False
        return True

    def _build_target(self, spec: "GpuBackendSpec", build_dir: Path,
                      env: dict[str, str]) -> bool:
        """Build *spec*'s adapter target in the already-configured *build_dir*."""
        cmake = self.cfg.expand(self.cfg.cmake_exe) or "cmake"
        argv = [cmake, "--build", str(build_dir), "--target", spec.adapter_target]
        if self._run(argv, None, env) != 0:
            console.warn(f"Building the {spec.vendor} adapter target failed.")
            return False
        return True

    def _run(self, argv: list[str], cwd: Path | None, env: dict[str, str]) -> int:
        """Run *argv* through the injected runner, turning a missing executable into a failure."""
        try:
            return self.runner.run(argv, cwd, env)
        except FileNotFoundError as exc:
            console.warn(f"Command not found: {argv[0]} ({exc})")
            return 1

    def _stage_binaries(self, spec: "GpuBackendSpec",
                        build_dir: Path) -> list[Path] | None:
        """Copy the built adapter binaries into a staging directory, or return None."""
        staging = self.work_root / f"{spec.vendor}-stage"
        shutil.rmtree(staging, ignore_errors=True)
        staging.mkdir(parents=True)
        output_dir = build_dir / "bin"
        staged: list[Path] = []
        for base_name in spec.adapter_binaries:
            for pattern in _binary_names(base_name, self.cfg.is_windows):
                matches = sorted(output_dir.glob(pattern))
                if not matches:
                    console.warn(
                        f"Expected {spec.vendor} adapter output {pattern} "
                        f"was not produced in {output_dir}.")
                    shutil.rmtree(staging, ignore_errors=True)
                    return None
                for match in matches:
                    destination = staging / match.name
                    shutil.copy2(match, destination)
                    staged.append(destination)
        return staged

    def _install_binaries(self, toolchain_root: Path, staged: list[Path]) -> bool:
        """Rename every staged binary into place, all or nothing.

        Any destination already present is first renamed aside, inside the
        staging directory, so it can be put back. Only once every existing
        destination has been moved aside does any staged file replace one;
        a failure at either stage rolls back everything already done, so
        *toolchain_root* ends up exactly as it started.
        """
        target_dir = toolchain_root / _bin_subdir(self.cfg.is_windows)
        target_dir.mkdir(parents=True, exist_ok=True)
        staging_dir = staged[0].parent

        previous: dict[Path, Path] = {}
        for source in staged:
            destination = target_dir / source.name
            if not destination.exists():
                continue
            previous_copy = staging_dir / (destination.name + ".previous")
            try:
                os.replace(destination, previous_copy)
            except OSError as exc:
                console.warn(
                    f"Could not move existing {destination} aside before install: {exc}")
                self._restore_previous(previous)
                return False
            previous[destination] = previous_copy

        installed: list[Path] = []
        for source in staged:
            destination = target_dir / source.name
            try:
                os.replace(source, destination)
            except OSError as exc:
                console.warn(f"Installing {destination} failed: {exc}")
                self._undo_installs(installed, previous)
                self._restore_previous(
                    {dest: prev for dest, prev in previous.items() if dest not in installed})
                return False
            installed.append(destination)

        for previous_copy in previous.values():
            try:
                previous_copy.unlink()
            except OSError:
                pass
        return True

    def _undo_installs(self, installed: list[Path], previous: dict[Path, Path]) -> None:
        """Undo every destination in *installed*: restore its previous file, or remove it."""
        for destination in installed:
            previous_copy = previous.get(destination)
            try:
                if previous_copy is not None:
                    os.replace(previous_copy, destination)
                else:
                    destination.unlink()
            except OSError as exc:
                state = f"restore from {previous_copy}" if previous_copy else "removal"
                console.warn(f"Rollback failed: {destination} left in place, {state} failed: {exc}")

    def _restore_previous(self, previous: dict[Path, Path]) -> None:
        """Restore every destination moved aside in *previous* to its original path."""
        for destination, previous_copy in previous.items():
            try:
                os.replace(previous_copy, destination)
            except OSError as exc:
                console.warn(
                    f"Rollback failed: {previous_copy} could not be restored to "
                    f"{destination}: {exc}")
