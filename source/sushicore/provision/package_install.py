# package_install.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Installs a built tree to a prefix and optionally archives it: the shared ``package`` command."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Protocol

from ..cmake_cache import cached_value
from . import home

#: The file that marks a prefix as one this command staged, so a later run may empty it.
K_STAGE_MARKER = ".sushi_package_stage"

#: The build type used when the tree's cache names none.
K_DEFAULT_CONFIG = "Release"

#: The line ``cmake --install`` prints for a file it copied.
K_INSTALLED_LINE = "-- Installing: "

#: The line ``cmake --install`` prints for a file it left as it was.
K_UP_TO_DATE_LINE = "-- Up-to-date: "


class _Console(Protocol):
    """The three console calls the installer makes."""

    def error(self, text: str) -> None:
        """Print an error line."""

    def command(self, text: str) -> None:
        """Print a command line."""

    def info(self, text: str) -> None:
        """Print an information line."""


@dataclass(frozen=True, slots=True)
class CapturedRun:
    """The exit code and the combined output of a command run with its output held back."""

    code: int
    output: str


def run_command(command: list[str], cwd: Path, env: Mapping[str, str] | None = None) -> int:
    """Run *command* in *cwd*; return its exit code, or 127 when it cannot start."""
    try:
        return subprocess.run(command, cwd=cwd).returncode
    except OSError:
        return 127


def capture_command(command: list[str], cwd: Path,
                    env: Mapping[str, str] | None = None) -> CapturedRun:
    """Run *command* in *cwd* with stdout and stderr held together; 127 when it cannot start."""
    try:
        done = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, errors="replace")
    except OSError as error:
        return CapturedRun(127, str(error))
    return CapturedRun(done.returncode, done.stdout or "")


def install_summary(output: str, prefix: Path) -> str:
    """Return one line counting the files a ``cmake --install`` *output* copied and kept.

    cmake prints a folder with the same prefix as a file, so a line counts only when its path
    is a file once the install is done.
    """
    def files(marker: str) -> int:
        """Return how many lines start with *marker* and name a file."""
        return sum(1 for line in output.splitlines()
                   if line.startswith(marker) and Path(line[len(marker):].strip()).is_file())

    return (f"Installed {files(K_INSTALLED_LINE)} files, {files(K_UP_TO_DATE_LINE)} up to date, "
            f"into {prefix}")


class PackageInstaller:
    """Runs ``cmake --install`` of a built tree into a prefix, then CPack when asked."""

    def __init__(self, console: _Console, cmake: str = "cmake",
                 run: Callable[..., int] = run_command,
                 capture: Callable[..., CapturedRun] = capture_command) -> None:
        """Bind the installer to its console and the commands it runs.

        Args:
            console: Receives the error, command and summary lines.
            cmake: The cmake executable; CPack is looked for beside it.
            run: Runs a command in a folder with its output shown; runs CPack; replaced in tests.
            capture: Runs a command in a folder with its output held back; runs the install;
                replaced in tests.
        """
        self._console = console
        self._cmake = cmake
        self._run = run
        self._capture = capture

    def install(self, root: Path, build_dir: Path, prefix: Path, *, archive: bool,
                force: bool) -> int:
        """Install the tree at *build_dir* into *prefix*; return an exit code.

        The tree must be built. A prefix that holds files this command did not stage is cleared
        only with *force*. The prefix is never the checkout or a protected folder.

        Args:
            root: The module's checkout.
            build_dir: The build tree to install from; relative paths are below *root*.
            prefix: Where to install; relative paths are below *root*.
            archive: Whether to run CPack after the install.
            force: Whether a prefix this command did not stage may be cleared.
        """
        tree = build_dir if build_dir.is_absolute() else root / build_dir
        target = (prefix if prefix.is_absolute() else root / prefix).resolve()
        if cached_value(tree, "CMAKE_HOME_DIRECTORY") is None:
            self._console.error(f"{tree} holds no configured build; build before packaging.")
            return 1
        refusal = self._refusal(root, target, force)
        if refusal:
            self._console.error(refusal)
            return 1
        self._clear(target)
        config = cached_value(tree, "CMAKE_BUILD_TYPE") or K_DEFAULT_CONFIG
        code = self._install_step([self._cmake, "--install", str(tree), "--prefix", str(target),
                                   "--config", config], root, target)
        if code != 0:
            return code
        (target / K_STAGE_MARKER).write_text("", encoding="utf-8")
        return self._step([self._cpack(), "--config", str(tree / "CPackConfig.cmake")],
                          tree) if archive else 0

    def _refusal(self, root: Path, target: Path, force: bool) -> str:
        """Return why *target* may not be the prefix, or '' when it may."""
        if target == root.resolve() or target in root.resolve().parents:
            return f"{target} is the checkout or holds it, and is never a prefix."
        if not home.is_removable_root(target):
            return f"{target} is a protected folder, and is never a prefix."
        held = target.is_dir() and any(target.iterdir())
        if held and not (target / K_STAGE_MARKER).is_file() and not force:
            return f"{target} holds files this command did not stage; pass --force to clear it."
        return ""

    @staticmethod
    def _clear(target: Path) -> None:
        """Empty *target*, creating it when it is absent."""
        if target.is_dir():
            for entry in target.iterdir():
                if entry.is_dir():
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
        target.mkdir(parents=True, exist_ok=True)

    def _step(self, command: list[str], cwd: Path) -> int:
        """Print and run one command; return its exit code."""
        self._console.command(" ".join(command))
        return self._run(command, cwd)

    def _install_step(self, command: list[str], cwd: Path, target: Path) -> int:
        """Print and run the install; print one summary line, or all of cmake's output on failure."""
        self._console.command(" ".join(command))
        result = self._capture(command, cwd)
        if result.code != 0:
            self._console.error(f"cmake --install exited {result.code}:\n{result.output.rstrip()}")
            return result.code
        self._console.info(install_summary(result.output, target))
        return 0

    def _cpack(self) -> str:
        """Return the cpack executable beside the configured cmake, else ``cpack``."""
        path = Path(self._cmake)
        sibling = path.with_name("cpack" + path.suffix)
        return str(sibling) if sibling.is_file() else "cpack"
