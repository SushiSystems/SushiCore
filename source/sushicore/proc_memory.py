# proc_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A command runner that records each command and replays scripted results, with no process."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .proc import K_TIMEOUT_EXIT_CODE, ConsoleLike, timed_out_message


@dataclass(frozen=True, slots=True)
class RecordedCommand:
    """One command a runner was asked to run.

    Attributes:
        argv: The command words as they were given.
        cwd: The folder the command was to run in.
        env: A copy of the environment given, or ``None`` when the caller gave none.
        drained: Whether the command ran through ``run_drained``.
        captured: Whether the command ran through ``capture``.
        timeout: The timeout a capture was given, or ``None``.
    """

    argv: tuple[str, ...]
    cwd: Path | None
    env: dict[str, str] | None
    drained: bool
    captured: bool = False
    timeout: float | None = None


@dataclass(frozen=True, slots=True)
class ScriptedRun:
    """What the runner answers to one command.

    Attributes:
        exit_code: The exit code returned.
        lines: The output lines a drained run prints, one per line, and a capture returns as stdout.
        stderr: The error output a capture returns.
        missing: Whether the executable is missing, as if it were on no PATH.
        timed_out: Whether a capture outlives its timeout.
    """

    exit_code: int = 0
    lines: tuple[str, ...] = ()
    stderr: str = ""
    missing: bool = False
    timed_out: bool = False


class RecordingRunner:
    """Records each command in order and answers the results scripted in advance.

    A command with no script left exits 0 and prints nothing. Nothing is spawned.

    Args:
        console: Receives the command line, the drained output and the not-found error.
        missing_exit_code: The code returned for a scripted missing executable.
    """

    def __init__(self, console: ConsoleLike, *, missing_exit_code: int = 1) -> None:
        """Start with no recorded commands and no scripted results."""
        self._console = console
        self._missing_exit_code = missing_exit_code
        self._scripts: list[ScriptedRun] = []
        self._commands: list[RecordedCommand] = []

    @property
    def commands(self) -> list[RecordedCommand]:
        """Return the commands recorded so far, in the order they were run."""
        return list(self._commands)

    def script(self, exit_code: int = 0, lines: tuple[str, ...] = (),
               stderr: str = "") -> "RecordingRunner":
        """Queue the answer to the next unanswered command and return this runner."""
        self._scripts.append(ScriptedRun(exit_code, tuple(lines), stderr))
        return self

    def script_missing(self) -> "RecordingRunner":
        """Queue a missing-executable answer for the next unanswered command."""
        self._scripts.append(ScriptedRun(missing=True))
        return self

    def script_timeout(self) -> "RecordingRunner":
        """Queue a capture that outlives its timeout for the next unanswered command."""
        self._scripts.append(ScriptedRun(timed_out=True))
        return self

    def resolve_exe(self, name: str, env: Mapping[str, str] | None = None) -> str:
        """Return *name* unchanged; no PATH is searched."""
        return name

    def run(self, cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> int:
        """Record *cmd* and return the next scripted exit code."""
        return self._answer(cmd, cwd, env, drained=False)

    def run_drained(self, cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> int:
        """Record *cmd*, print the next scripted lines unparsed and return its exit code."""
        return self._answer(cmd, cwd, env, drained=True)

    def capture(self, cmd: list[str], cwd: Path | None = None,
                env: dict[str, str] | None = None,
                timeout: float | None = None) -> tuple[int, str, str]:
        """Record *cmd* quietly and return the next scripted exit code, lines as stdout, and stderr."""
        self._commands.append(RecordedCommand(
            tuple(cmd), cwd, dict(env) if env is not None else None, drained=False, captured=True,
            timeout=timeout))
        scripted = self._scripts.pop(0) if self._scripts else ScriptedRun()
        if scripted.timed_out:
            return K_TIMEOUT_EXIT_CODE, "", timed_out_message(cmd[0], timeout)
        if scripted.missing:
            return self._missing_exit_code, "", f"Executable not found: '{cmd[0]}'"
        stdout = "".join(f"{line}\n" for line in scripted.lines)
        return scripted.exit_code, stdout, scripted.stderr

    def _answer(self, cmd: list[str], cwd: Path, env: dict[str, str] | None,
                *, drained: bool) -> int:
        """Record one command, then play the script queued for it."""
        self._commands.append(RecordedCommand(
            tuple(cmd), cwd, dict(env) if env is not None else None, drained))
        self._console.command(shlex.join(cmd))
        scripted = self._scripts.pop(0) if self._scripts else ScriptedRun()
        if scripted.missing:
            self._console.error(f"Executable not found: '{cmd[0]}'.")
            return self._missing_exit_code
        if drained:
            for line in scripted.lines:
                self._console.console.print(line, markup=False, highlight=False,
                                            soft_wrap=True)
        return scripted.exit_code
