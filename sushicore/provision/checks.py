# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The stock doctor checks every module CLI registers."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

from sushicore.provision import probe
from sushicore.provision.config import ProvisionConfig
from sushicore.provision.doctor import Check, CheckResult, FunctionCheck, State
from sushicore.provision.fragments import IDependencySource
from sushicore.provision.toolchains.stamp import TOOLCHAIN_STAMP

#: Timeout, in seconds, for every ``--version`` probe a check runs.
_VERSION_TIMEOUT = 15


def _first_version_line(exe: str) -> str:
    """Return the first line ``<exe> --version`` prints, or '' when it cannot run."""
    try:
        result = subprocess.run([exe, "--version"], capture_output=True, text=True,
                                 timeout=_VERSION_TIMEOUT)
    except (OSError, ValueError, subprocess.SubprocessError):
        return ""
    lines = (result.stdout or result.stderr).strip().splitlines()
    return lines[0].strip() if lines else ""


def python_check(minimum: tuple[int, int] = (3, 10)) -> FunctionCheck:
    """Return a check passing when this interpreter meets *minimum*."""
    def fn() -> CheckResult:
        version = sys.version_info[:2]
        detail = f"{sys.executable} (Python {sys.version_info.major}.{sys.version_info.minor})"
        if version >= minimum:
            return CheckResult(State.OK, detail)
        return CheckResult(State.FAIL, detail, f"install Python {minimum[0]}.{minimum[1]}+")
    return FunctionCheck("python", "build", True, fn)


def tool_check(name: str, exe: str, group: str = "build", required: bool = True,
               fix: str = "") -> FunctionCheck:
    """Return a check passing when ``exe`` runs, its detail from ``<exe> --version``."""
    def fn() -> CheckResult:
        if not probe.binary_works(exe):
            return CheckResult(State.FAIL, f"'{exe}' not found on PATH", fix)
        return CheckResult(State.OK, _first_version_line(exe) or exe)
    return FunctionCheck(name, group, required, fn)


def compiler_check(cfg: ProvisionConfig, fix: str = "") -> FunctionCheck:
    """Return a check reporting every C++ compiler found, MSVC/Clang/GCC each in turn."""
    def fn() -> CheckResult:
        compilers: list[tuple[str, str]] = []
        if cfg.platform == "windows":
            dev_shell = os.environ.get("VSINSTALLDIR")
            configured = cfg.expand(cfg.vs_vcvars) if cfg.vs_vcvars else ""
            found, info = (True, dev_shell) if dev_shell else (
                bool(configured) and Path(configured).is_file(), configured)
            if found:
                compilers.append(("MSVC", info))
        for label, exe in (("Clang", "clang++"), ("GCC", "g++")):
            line = _first_version_line(exe)
            if line:
                compilers.append((label, line))
        if compilers:
            return CheckResult(State.OK, "; ".join(f"{lbl}: {info}" for lbl, info in compilers))
        detail = ("no MSVC (VSINSTALLDIR/vs_vcvars), clang++ or g++ found"
                  if cfg.platform == "windows" else "no clang++ or g++ on PATH")
        return CheckResult(State.FAIL, detail, fix)
    return FunctionCheck("c++ compiler", "build", True, fn)


def python_module_check(module: str, group: str, required: bool, fix: str) -> FunctionCheck:
    """Return a check passing when *module* is importable, without importing it."""
    def fn() -> CheckResult:
        try:
            found = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            found = False
        if found:
            return CheckResult(State.OK, module)
        return CheckResult(State.FAIL, f"module '{module}' not importable", fix)
    return FunctionCheck(module, group, required, fn)


def path_check(name: str, path: Path, group: str, required: bool, fix: str) -> FunctionCheck:
    """Return a check passing when *path* exists on disk."""
    def fn() -> CheckResult:
        if path.exists():
            return CheckResult(State.OK, str(path))
        return CheckResult(State.FAIL, f"{path} missing", fix)
    return FunctionCheck(name, group, required, fn)


def fragment_check(source: IDependencySource, platform: str, gpu: bool,
                    fix: str) -> FunctionCheck:
    """Return a check reporting every selected dependency whose ``check_cmd`` fails."""
    def fn() -> CheckResult:
        failing: list[str] = []
        required_failed = False
        for dep in source.selected(platform, gpu):
            if not dep.check_cmd:
                continue
            try:
                ok = subprocess.run(dep.check_cmd, capture_output=True,
                                     timeout=_VERSION_TIMEOUT).returncode == 0
            except (OSError, ValueError, TypeError, subprocess.TimeoutExpired):
                ok = False
            if not ok:
                failing.append(dep.name)
                required_failed = required_failed or dep.required
        if not failing:
            return CheckResult(State.OK, "all checked dependencies satisfied")
        detail = "not satisfied: " + ", ".join(failing)
        return CheckResult(State.FAIL if required_failed else State.WARN, detail, fix)
    return FunctionCheck("dependencies", "build", True, fn)


def stamp_check(root: Path) -> FunctionCheck:
    """Return a check warning about a toolchain directory under *root* with no stamp."""
    def fn() -> CheckResult:
        toolchains = root / "toolchains"
        if not toolchains.is_dir():
            return CheckResult(State.OK, "no toolchains installed")
        try:
            entries = sorted(toolchains.iterdir())
        except OSError as exc:
            return CheckResult(State.WARN, f"cannot read {toolchains}: {exc}")
        unstamped = [d.name for d in entries
                     if d.is_dir() and not (d / TOOLCHAIN_STAMP).is_file()]
        if not unstamped:
            return CheckResult(State.OK, "every installed toolchain is stamped")
        detail = "unstamped toolchain(s): " + ", ".join(unstamped)
        return CheckResult(State.WARN, detail, "reinstall to record a toolchain stamp")
    return FunctionCheck("toolchain stamps", "build", False, fn)


def standard_checks(cfg: ProvisionConfig, fix: str) -> list[Check]:
    """Return the checks every module CLI registers: python, cmake, ctest, ninja, compiler, git."""
    checks = [
        python_check(),
        tool_check("cmake", cfg.cmake_exe or "cmake", group="build", required=True, fix=fix),
        tool_check("ctest", cfg.ctest_exe or "ctest", group="test", required=True, fix=fix),
    ]
    if cfg.ninja_exe or shutil.which("ninja"):
        ninja_exe = cfg.ninja_exe or "ninja"
        checks.append(tool_check("ninja", ninja_exe, group="build", required=True, fix=fix))
    checks.append(compiler_check(cfg, fix=fix))
    checks.append(tool_check("git", "git", group="build", required=False))
    return checks
