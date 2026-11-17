# checks.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The stock doctor checks every module CLI registers."""

from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path
from typing import Callable, Mapping, Sequence

from sushicore.proc import CommandRunner, did_not_run
from sushicore.provision import probe
from sushicore.provision.config import ProvisionConfig
from sushicore.provision.doctor import Check, CheckResult, FunctionCheck, State
from sushicore.provision.download_verifier import unpinned_downloads
from sushicore.provision.fragments import Dependency, IDependencySource
from sushicore.provision.process_run import provision_runner
from sushicore.provision.selection import required_groups
from sushicore.provision.target import target_of
from sushicore.provision.toolchains.stamp import TOOLCHAIN_STAMP

#: Timeout, in seconds, for every ``--version`` probe a check runs.
_VERSION_TIMEOUT = 15


def _first_version_line(exe: str, runner: CommandRunner | None = None) -> str:
    """Return the first line ``<exe> --version`` prints, or '' when it cannot run."""
    code, out, err = (runner or provision_runner()).capture([exe, "--version"],
                                                            timeout=_VERSION_TIMEOUT)
    if did_not_run(exe, code, err):
        return ""
    lines = (out or err).strip().splitlines()
    return lines[0].strip() if lines else ""


def python_check(minimum: tuple[int, int] = (3, 10), version: tuple[int, int] | None = None,
                 executable: str | None = None) -> FunctionCheck:
    """Return a check passing when this interpreter meets *minimum*.

    Args:
        version: The ``(major, minor)`` to judge; the running interpreter's when ``None``.
        executable: The interpreter path to report; the running one's when ``None``.
    """
    def fn() -> CheckResult:
        actual = version or tuple(sys.version_info[:2])
        path = executable or sys.executable
        detail = f"{path} (Python {actual[0]}.{actual[1]})"
        version_ok = actual >= minimum
        if version_ok:
            return CheckResult(State.OK, detail)
        return CheckResult(State.FAIL, detail, f"install Python {minimum[0]}.{minimum[1]}+")
    return FunctionCheck("python", "build", True, fn)


def tool_check(name: str, exe: str, group: str = "build", required: bool = True,
               fix: str = "", works: Callable[[str], bool] | None = None,
               runner: CommandRunner | None = None) -> FunctionCheck:
    """Return a check passing when ``exe`` runs, its detail from ``<exe> --version``.

    Args:
        works: Asked whether *exe* runs; ``probe.binary_works`` through *runner* when ``None``.
        runner: Runs the version probe; the provision runner when ``None``.
    """
    def fn() -> CheckResult:
        runs = works or (lambda name: probe.binary_works(name, runner))
        if not runs(exe):
            return CheckResult(State.FAIL, f"'{exe}' not found on PATH", fix)
        return CheckResult(State.OK, _first_version_line(exe, runner) or exe)
    return FunctionCheck(name, group, required, fn)


def compiler_check(cfg: ProvisionConfig, fix: str = "",
                   runner: CommandRunner | None = None) -> FunctionCheck:
    """Return a check reporting every C++ compiler found, MSVC/Clang/GCC each in turn.

    Args:
        runner: Runs the version probes; the provision runner when ``None``.
    """
    def fn() -> CheckResult:
        target = target_of(cfg)
        compilers = target.host_compilers(cfg)
        for label, exe in (("Clang", "clang++"), ("GCC", "g++")):
            line = _first_version_line(exe, runner)
            if line:
                compilers.append((label, line))
        if compilers:
            return CheckResult(State.OK, "; ".join(f"{lbl}: {info}" for lbl, info in compilers))
        return CheckResult(State.FAIL, target.no_compiler_detail, fix)
    return FunctionCheck("c++ compiler", "build", True, fn)


def python_module_check(module: str, group: str, required: bool, fix: str,
                        finder: Callable[[str], object | None] | None = None) -> FunctionCheck:
    """Return a check passing when *module* is importable, without importing it.

    Args:
        finder: Asked for the spec of *module*, ``None`` when absent; ``importlib.util.find_spec``
            when ``None``.
    """
    def fn() -> CheckResult:
        try:
            found = (finder or importlib.util.find_spec)(module) is not None
        except (ImportError, ValueError):
            found = False
        if found:
            return CheckResult(State.OK, module)
        return CheckResult(State.FAIL, f"module '{module}' not importable", fix)
    return FunctionCheck(module, group, required, fn)


def path_check(name: str, path: Path, group: str, required: bool, fix: str,
               exists: Callable[[Path], bool] | None = None) -> FunctionCheck:
    """Return a check passing when *path* exists.

    Args:
        exists: Asked whether *path* exists; ``Path.exists`` when ``None``.
    """
    def fn() -> CheckResult:
        if (exists or Path.exists)(path):
            return CheckResult(State.OK, str(path))
        return CheckResult(State.FAIL, f"{path} missing", fix)
    return FunctionCheck(name, group, required, fn)


def fragment_check(source: IDependencySource, platform: str, gpu: bool, fix: str,
                   installed: Callable[[Dependency], bool] | None = None,
                   runner: CommandRunner | None = None) -> FunctionCheck:
    """Return a check reporting every selected dependency whose ``check_cmd`` fails.

    Args:
        installed: Asked about a dependency whose ``check_cmd`` failed; a true
            answer passes it, as the install inventory does.
        runner: Runs each ``check_cmd``, which passes when it exits zero within the version
            timeout; the provision runner when ``None``.
    """
    def fn() -> CheckResult:
        run = runner or provision_runner()
        failing: list[str] = []
        required_failed = False
        for dep in source.selected(platform, gpu):
            if not dep.check_cmd:
                continue
            ok = run.capture(list(dep.check_cmd), timeout=_VERSION_TIMEOUT)[0] == 0
            if not ok and installed is not None:
                ok = installed(dep)
            if not ok:
                failing.append(dep.name)
                required_failed = required_failed or dep.required
        if not failing:
            return CheckResult(State.OK, "all checked dependencies satisfied")
        detail = "not satisfied: " + ", ".join(failing)
        return CheckResult(State.FAIL if required_failed else State.WARN, detail, fix)
    return FunctionCheck("dependencies", "build", True, fn)


def modules_check(missing: Sequence[tuple[str, str]], fix: str) -> FunctionCheck:
    """Return a check failing for each ``(module, wanted by)`` pair with no checkout."""
    def fn() -> CheckResult:
        if not missing:
            return CheckResult(State.OK, "every module this one builds on is checked out")
        named = ", ".join(f"{module} (wanted by {owner})" for module, owner in missing)
        return CheckResult(State.FAIL, f"no checkout of: {named}", fix)
    return FunctionCheck("modules", "build", True, fn)


def capability_check(source: IDependencySource, present: Mapping[str, bool],
                     fix: str) -> FunctionCheck:
    """Return a check failing for each required toolchain capability nothing present provides."""
    def fn() -> CheckResult:
        declared = required_groups(source)
        if not declared:
            return CheckResult(State.OK, "no toolchain required")
        satisfied: list[str] = []
        unsatisfied: list[str] = []
        for capability, members in declared.items():
            found = [member for member in members if present.get(member)]
            alone = members == [capability]
            if found:
                satisfied.append(capability if alone else f"{capability}: {', '.join(found)}")
            elif alone:
                unsatisfied.append(f"{capability} is not installed")
            else:
                unsatisfied.append(f"{capability}: none of {', '.join(members)}")
        if unsatisfied:
            return CheckResult(State.FAIL, "; ".join(unsatisfied), fix)
        return CheckResult(State.OK, "; ".join(satisfied))
    return FunctionCheck("toolchains", "build", True, fn)


def _disk_stamps(toolchains: Path) -> dict[str, bool] | None:
    """Return each toolchain folder under *toolchains* mapped to whether it holds a stamp.

    Returns ``None`` when *toolchains* is not a folder; raises ``OSError`` when it cannot be read.
    """
    if not toolchains.is_dir():
        return None
    return {d.name: (d / TOOLCHAIN_STAMP).is_file()
            for d in sorted(toolchains.iterdir()) if d.is_dir()}


def stamp_check(root: Path,
                stamps: Callable[[Path], Mapping[str, bool] | None] | None = None) -> FunctionCheck:
    """Return a check warning about a toolchain directory under *root* with no stamp.

    Args:
        stamps: Asked for the ``toolchains`` folder of *root*; answers each toolchain folder
            mapped to whether it is stamped, ``None`` when there is no folder, or raises
            ``OSError``. A disk reader when ``None``.
    """
    def fn() -> CheckResult:
        toolchains = root / "toolchains"
        try:
            found = (stamps or _disk_stamps)(toolchains)
        except OSError as exc:
            return CheckResult(State.WARN, f"cannot read {toolchains}: {exc}")
        if found is None:
            return CheckResult(State.OK, "no toolchains installed")
        unstamped = [name for name, stamped in found.items() if not stamped]
        if not unstamped:
            return CheckResult(State.OK, "every installed toolchain is stamped")
        detail = "unstamped toolchain(s): " + ", ".join(unstamped)
        return CheckResult(State.WARN, detail, "reinstall to record a toolchain stamp")
    return FunctionCheck("toolchain stamps", "build", False, fn)


def digest_check(source: IDependencySource, platform: str) -> FunctionCheck:
    """Return a check warning about each download *platform* fetches with no pinned digest."""
    def fn() -> CheckResult:
        declared = {dep.name for dep in source.all()}
        unpinned = unpinned_downloads(declared, source.digests(platform), platform)
        if not unpinned:
            return CheckResult(State.OK, "every download carries a pinned sha256")
        detail = "downloaded unverified, no sha256 pinned: " + ", ".join(unpinned)
        return CheckResult(State.WARN, detail,
                           "pin sha256 in each entry of the dependency manifest")
    return FunctionCheck("download digests", "build", False, fn)


def standard_checks(cfg: ProvisionConfig, fix: str,
                    runner: CommandRunner | None = None) -> list[Check]:
    """Return the checks every module CLI registers: python, cmake, ctest, ninja, compiler, git.

    Args:
        runner: Runs every version probe; the provision runner when ``None``.
    """
    checks = [
        python_check(),
        tool_check("cmake", cfg.cmake_exe or "cmake", group="build", required=True, fix=fix,
                   runner=runner),
        tool_check("ctest", cfg.ctest_exe or "ctest", group="test", required=True, fix=fix,
                   runner=runner),
    ]
    if cfg.ninja_exe or shutil.which("ninja"):
        ninja_exe = cfg.ninja_exe or "ninja"
        checks.append(tool_check("ninja", ninja_exe, group="build", required=True, fix=fix,
                                runner=runner))
    checks.append(compiler_check(cfg, fix=fix, runner=runner))
    checks.append(tool_check("git", "git", group="build", required=False, runner=runner))
    return checks
