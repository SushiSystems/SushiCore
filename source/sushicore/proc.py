# proc.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The one brick that spawns child processes on behalf of a CLI.

Every operation hands a child's output to the console line by line, so in machine mode
it is an event and never a line on stdout.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Mapping, Protocol

K_TIMEOUT_EXIT_CODE = 124
"""The exit code a capture returns when its command outlives its timeout, as GNU `timeout` returns."""

K_QUIET_TAIL_LINES = 20
"""How many of the last output lines a quiet run shows when its command fails."""


class RichConsoleLike(Protocol):
    """The one Rich console method this needs, so `console` is not typed `object`."""

    def print(self, *objects: object, **kwargs: object) -> None: ...


class ConsoleLike(Protocol):
    """The slice of a CLI's console module this needs."""

    console: RichConsoleLike

    def command(self, text: str) -> None: ...

    def info(self, text: str) -> None: ...

    def error(self, text: str) -> None: ...

    def warn(self, text: str) -> None: ...

    def is_machine(self) -> bool: ...


def emit_output_line(console: ConsoleLike, line: str) -> None:
    """Hand one line of a child's output to *console*.

    In machine mode the line is an `info` event. Otherwise it is printed with markup off,
    because child output carries literal "[file:line]" and "[[nodiscard]]" tags that Rich
    would parse as console markup and silently drop.
    """
    if console.is_machine():
        console.info(line)
        return
    console.console.print(line, markup=False, highlight=False, soft_wrap=True)


class CommandRunner(Protocol):
    """The surface callers use to run external commands: path lookup, run, run drained and capture."""

    def resolve_exe(self, name: str, env: Mapping[str, str] | None = None) -> str:
        """Return the executable *name* resolved against *env*'s PATH, or *name* itself."""
        ...

    def run(self, cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> int:
        """Run *cmd* in *cwd* and return its exit code; in machine mode it runs as `run_drained`."""
        ...

    def run_drained(self, cmd: list[str], cwd: Path | None, env: dict[str, str] | None = None,
                    *, dry_run: bool = False, check: bool = False) -> int:
        """Run *cmd*, re-emit its output line by line and return its exit code.

        A dry run echoes the command, starts nothing and returns 0. With *check*, a non-zero
        exit code is also reported as one error.
        """
        ...

    def run_quiet(self, cmd: list[str], cwd: Path | None = None,
                  env: dict[str, str] | None = None, *, dry_run: bool = False) -> bool:
        """Run *cmd* showing no output unless it fails, and return whether it exited 0.

        A failed run shows the last `K_QUIET_TAIL_LINES` lines of its output. A dry run echoes
        the command, starts nothing and returns True.
        """
        ...

    def capture(self, cmd: list[str], cwd: Path | None = None,
                env: dict[str, str] | None = None,
                timeout: float | None = None) -> tuple[int, str, str]:
        """Run *cmd* quietly and return its exit code, stdout and stderr.

        A command still running after *timeout* seconds is stopped, and the capture returns
        `K_TIMEOUT_EXIT_CODE` with a stderr that says it timed out.
        """
        ...


class Runner:
    """Runs external commands and says what it ran; implements :class:`CommandRunner`.

    @param console A CLI's console module.
    @param program The CLI's command name ("sr", "se", ...), used in guidance.
    @param missing_exit_code Code `run` and `run_drained` return for a missing executable.
    @param catch_interrupt Whether `run` and `run_drained` turn Ctrl+C into a warning and 130.
    """

    __slots__ = ("_console", "_program", "_missing_exit_code", "_catch_interrupt")

    def __init__(self, console: ConsoleLike, program: str, *,
                 missing_exit_code: int = 1, catch_interrupt: bool = False) -> None:
        self._console = console
        self._program = program
        self._missing_exit_code = missing_exit_code
        self._catch_interrupt = catch_interrupt

    def resolve_exe(self, name: str, env: Mapping[str, str] | None = None) -> str:
        """The full path to *name* from *env*'s PATH, or *name* itself.

        Resolving to a full path is what stops subprocess.CreateProcess from
        doing its own PATH lookup against a plain-dict env. On Windows that dict
        can hold both "Path" (from os.environ) and "PATH" (from a vcvars
        overlay); subprocess sees two keys and picks between them
        unpredictably, so a tool on one of the two is intermittently not found.

        Every PATH-spelled key is searched, joined in the env's own iteration
        order. Reading only the first one would move that same coin flip into
        this function rather than remove it: whichever spelling `next()`
        happened to reach would be searched and the other silently ignored,
        which is how a tool that is genuinely on the path comes back as a bare
        name. The union can only find a tool the single-key read misses.
        """
        if env is None:
            return shutil.which(name) or name
        paths = [v for k, v in env.items() if k.upper() == "PATH" and v]
        env_path = os.pathsep.join(paths) if paths else None
        return shutil.which(name, path=env_path) or shutil.which(name) or name

    def _not_found(self, name: str) -> None:
        self._console.error(
            f"Executable not found: '{name}'.\n"
            f"  - it is not on PATH and no explicit path is configured.\n"
            f"  - set its path in config.local.toml "
            f"(e.g. cmake_exe / ctest_exe / ninja_exe), or\n"
            f"  - run `{self._program} config` to see what the CLI resolved.")

    def _begin(self, cmd: list[str], env: Mapping[str, str] | None,
               dry_run: bool) -> list[str] | None:
        """Echo *cmd* and return it with its executable resolved, or None on a dry run."""
        resolved = list(cmd)
        resolved[0] = self.resolve_exe(cmd[0], env)
        self._console.command(subprocess.list2cmdline(resolved))
        if dry_run:
            self._console.info("(dry-run) not executed")
            return None
        return resolved

    def _interrupted(self) -> int:
        """Warn that the child was interrupted and return 130."""
        self._console.warn("Interrupted.")
        return 130

    def run(self, cmd: list[str], cwd: Path,
            env: dict[str, str] | None = None) -> int:
        """Run *cmd*, letting the child inherit this process's stdout.

        In machine mode the child must not reach stdout, so the run is `run_drained`.
        """
        if self._console.is_machine():
            return self.run_drained(cmd, cwd, env)
        resolved = list(cmd)
        resolved[0] = self.resolve_exe(cmd[0], env)
        self._console.command(subprocess.list2cmdline(resolved))
        try:
            return subprocess.run(resolved, cwd=str(cwd), env=env).returncode
        except FileNotFoundError:
            self._not_found(cmd[0])
            return self._missing_exit_code
        except KeyboardInterrupt:
            if not self._catch_interrupt:
                raise
            return self._interrupted()

    def run_drained(self, cmd: list[str], cwd: Path | None, env: dict[str, str] | None = None,
                    *, dry_run: bool = False, check: bool = False) -> int:
        """Run *cmd* with its output piped here and re-emitted line by line.

        Draining the pipe ourselves is what keeps ctest's gtest_discover_tests
        step reliable on Windows: when ctest's stdout is an inherited, slowly
        drained pipe, the discovery child intermittently stalls and registers
        nothing, surfacing as "No tests were found".
        """
        resolved = self._begin(cmd, env, dry_run)
        if resolved is None:
            return 0
        try:
            process = subprocess.Popen(
                resolved, cwd=_cwd_text(cwd), env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1)
        except FileNotFoundError:
            self._not_found(cmd[0])
            return self._missing_exit_code
        try:
            if process.stdout is not None:
                for line in process.stdout:
                    emit_output_line(self._console, line.rstrip("\n"))
            code = process.wait()
        except KeyboardInterrupt:
            if not self._catch_interrupt:
                raise
            process.terminate()
            process.wait()
            return self._interrupted()
        if check and code != 0:
            self._console.error(f"Command failed ({code}).")
        return code

    def run_quiet(self, cmd: list[str], cwd: Path | None = None,
                  env: dict[str, str] | None = None, *, dry_run: bool = False) -> bool:
        """Run *cmd* showing no output unless it fails, and return whether it exited 0.

        A missing executable is reported as one error and counts as a failure.
        """
        resolved = self._begin(cmd, env, dry_run)
        if resolved is None:
            return True
        try:
            done = subprocess.run(
                resolved, cwd=_cwd_text(cwd), env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace")
        except FileNotFoundError:
            self._not_found(cmd[0])
            return False
        except KeyboardInterrupt:
            if not self._catch_interrupt:
                raise
            self._interrupted()
            return False
        if done.returncode != 0:
            for line in (done.stdout or "").splitlines()[-K_QUIET_TAIL_LINES:]:
                emit_output_line(self._console, line)
        return done.returncode == 0

    def capture(self, cmd: list[str], cwd: Path | None = None,
                env: dict[str, str] | None = None,
                timeout: float | None = None) -> tuple[int, str, str]:
        """Run *cmd* quietly and return its exit code, stdout and stderr.

        A command still running after *timeout* seconds is stopped, and the capture returns
        `K_TIMEOUT_EXIT_CODE`, the output read until then, and a stderr that says it timed out.
        """
        resolved = list(cmd)
        resolved[0] = self.resolve_exe(cmd[0], env)
        try:
            result = subprocess.run(resolved, cwd=str(cwd) if cwd else None, env=env,
                                    capture_output=True, text=True, errors="replace",
                                    timeout=timeout)
        except subprocess.TimeoutExpired as expired:
            stdout = expired.stdout if isinstance(expired.stdout, str) else ""
            return K_TIMEOUT_EXIT_CODE, stdout, timed_out_message(cmd[0], timeout)
        except FileNotFoundError:
            return self._missing_exit_code, "", f"Executable not found: '{cmd[0]}'"
        except KeyboardInterrupt:
            if not self._catch_interrupt:
                raise
            return self._interrupted(), "", ""
        return result.returncode, result.stdout, result.stderr


def _cwd_text(cwd: Path | None) -> str | None:
    """Return *cwd* as the text `subprocess` takes, or None for the current folder."""
    return None if cwd is None else str(cwd)


def timed_out_message(program: str, timeout: float | None) -> str:
    """Return the stderr a capture gives for a command stopped after *timeout* seconds."""
    if timeout is None:
        return f"'{program}' timed out"
    return f"'{program}' timed out after {timeout:g} s"
