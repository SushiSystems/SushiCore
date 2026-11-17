# proc_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A command runner that records each command and replays scripted results, with no process."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Mapping, final

from .proc import (K_QUIET_TAIL_LINES, K_TIMEOUT_EXIT_CODE, ConsoleLike, emit_output_line,
                   not_found_message, timed_out_message)


@final
@dataclass(frozen=True, slots=True)
class RecordedCommand:
    """One command a runner was asked to run.

    Attributes:
        argv: The command words as they were given.
        cwd: The folder the command was to run in.
        env: A copy of the environment given, or ``None`` when the caller gave none.
        drained: Whether the command ran through ``run_drained``, or through ``run`` in machine mode.
        captured: Whether the command ran through ``capture``.
        timeout: The timeout a capture was given, or ``None``.
        quiet: Whether the command ran through ``run_quiet``.
        input_text: The text a capture wrote to the command's stdin, or ``None``.
        stdin_given: Whether a run was given a file to read as its stdin.
    """

    argv: tuple[str, ...]
    cwd: Path | None
    env: dict[str, str] | None
    drained: bool
    captured: bool = False
    timeout: float | None = None
    quiet: bool = False
    input_text: str | None = None
    stdin_given: bool = False


@final
@dataclass(frozen=True, slots=True)
class ScriptedRun:
    """What the runner answers to one command.

    Attributes:
        exit_code: The exit code returned.
        lines: The output lines a drained run prints, one per line, and a capture returns as stdout.
            A failed quiet run shows the last `K_QUIET_TAIL_LINES` of them.
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

    def run(self, cmd: list[str], cwd: Path | None, env: dict[str, str] | None = None,
            *, timeout: float | None = None, stdin: IO[str] | None = None) -> int:
        """Record *cmd* and return the next scripted exit code; in machine mode it runs drained.

        A scripted timeout answers `K_TIMEOUT_EXIT_CODE`, as a run that outlives *timeout* does.
        The record says whether a *stdin* was given; the file is not read.
        """
        return self._answer(cmd, cwd, env, drained=self._console.is_machine(), timeout=timeout,
                            stdin_given=stdin is not None)

    def run_drained(self, cmd: list[str], cwd: Path | None, env: dict[str, str] | None = None,
                    *, dry_run: bool = False, check: bool = False) -> int:
        """Record *cmd*, hand the next scripted lines to the console and return its exit code."""
        if dry_run:
            return self._dry_run(cmd, 0)
        code = self._answer(cmd, cwd, env, drained=True)
        if check and code != 0:
            self._console.error(f"Command failed ({code}).")
        return code

    def run_quiet(self, cmd: list[str], cwd: Path | None = None,
                  env: dict[str, str] | None = None, *, dry_run: bool = False) -> bool:
        """Record *cmd*, show the tail of its scripted lines when it fails and return whether it passed."""
        if dry_run:
            return self._dry_run(cmd, True)
        scripted = self._play(cmd, cwd, env, drained=False, quiet=True)
        if scripted.missing:
            return False
        if scripted.exit_code != 0:
            for line in scripted.lines[-K_QUIET_TAIL_LINES:]:
                emit_output_line(self._console, line)
        return scripted.exit_code == 0

    def capture(self, cmd: list[str] | str, cwd: Path | None = None,
                env: dict[str, str] | None = None, timeout: float | None = None,
                *, input_text: str | None = None,
                encoding: str | None = None) -> tuple[int, str, str]:
        """Record *cmd* quietly and return the next scripted exit code, lines as stdout, and stderr."""
        argv = (cmd,) if isinstance(cmd, str) else tuple(cmd)
        program = cmd.split(maxsplit=1)[0] if isinstance(cmd, str) and cmd.strip() else argv[0]
        self._commands.append(RecordedCommand(
            argv, cwd, dict(env) if env is not None else None, drained=False, captured=True,
            timeout=timeout, input_text=input_text))
        scripted = self._scripts.pop(0) if self._scripts else ScriptedRun()
        if scripted.timed_out:
            return K_TIMEOUT_EXIT_CODE, "", timed_out_message(program, timeout)
        if scripted.missing:
            return self._missing_exit_code, "", not_found_message(program)
        stdout = "".join(f"{line}\n" for line in scripted.lines)
        return scripted.exit_code, stdout, scripted.stderr

    def capture_bytes(self, cmd: list[str], cwd: Path | None = None,
                      env: dict[str, str] | None = None,
                      timeout: float | None = None) -> tuple[int, bytes, bytes]:
        """Record *cmd* quietly and return the next scripted answer as UTF-8 bytes."""
        code, stdout, stderr = self.capture(cmd, cwd, env, timeout)
        return code, stdout.encode(), stderr.encode()

    def _answer(self, cmd: list[str], cwd: Path | None, env: dict[str, str] | None,
                *, drained: bool, timeout: float | None = None, stdin_given: bool = False) -> int:
        """Record one command, then play the script queued for it."""
        scripted = self._play(cmd, cwd, env, drained=drained, quiet=False, timeout=timeout,
                              stdin_given=stdin_given)
        if scripted.missing:
            return self._missing_exit_code
        if scripted.timed_out:
            return K_TIMEOUT_EXIT_CODE
        if drained:
            for line in scripted.lines:
                emit_output_line(self._console, line)
        return scripted.exit_code

    def _play(self, cmd: list[str], cwd: Path | None, env: dict[str, str] | None,
              *, drained: bool, quiet: bool, timeout: float | None = None,
              stdin_given: bool = False) -> ScriptedRun:
        """Record *cmd*, echo it, report a scripted missing executable and return the script."""
        self._commands.append(RecordedCommand(
            tuple(cmd), cwd, dict(env) if env is not None else None, drained, quiet=quiet,
            timeout=timeout, stdin_given=stdin_given))
        self._console.command(shlex.join(cmd))
        scripted = self._scripts.pop(0) if self._scripts else ScriptedRun()
        if scripted.missing:
            self._console.error(f"Executable not found: '{cmd[0]}'.")
        return scripted

    def _dry_run(self, cmd: list[str], answer: int | bool) -> int | bool:
        """Echo *cmd* as a dry run does, record nothing and return *answer*."""
        self._console.command(shlex.join(cmd))
        self._console.info("(dry-run) not executed")
        return answer
