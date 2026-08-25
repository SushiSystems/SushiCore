"""Spawning a child process on behalf of a CLI.

Five modules carried a copy of this. Stripped of docstrings the copies differed
in exactly two places: the program name in the not-found message, and whether
Rich was told not to parse the child's output as markup. The first is what the
profile is for. The second was a defect in three of them.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Mapping, Protocol


class RichConsoleLike(Protocol):
    """The one Rich console method this needs, so `console` is not typed `object`."""

    def print(self, *objects: object, **kwargs: object) -> None: ...


class ConsoleLike(Protocol):
    """The slice of a CLI's console module this needs."""

    console: RichConsoleLike

    def command(self, text: str) -> None: ...

    def error(self, text: str) -> None: ...


class Runner:
    """Runs external commands and says what it ran.

    @param console A CLI's console module.
    @param program The CLI's command name ("sr", "se", ...), used in guidance.
    """

    __slots__ = ("_console", "_program")

    def __init__(self, console: ConsoleLike, program: str) -> None:
        self._console = console
        self._program = program

    def resolve_exe(self, name: str, env: Mapping[str, str] | None = None) -> str:
        """The full path to *name* from *env*'s PATH, or *name* itself.

        Resolving to a full path is what stops subprocess.CreateProcess from
        doing its own PATH lookup against a plain-dict env. On Windows that dict
        can hold both "Path" (from os.environ) and "PATH" (from a vcvars
        overlay); subprocess sees two keys and picks between them unpredictably,
        so a tool on one of the two is intermittently not found.
        """
        if env is None:
            return shutil.which(name) or name
        env_path = next((v for k, v in env.items() if k.upper() == "PATH"), None)
        return shutil.which(name, path=env_path) or shutil.which(name) or name

    def _not_found(self, name: str) -> None:
        self._console.error(
            f"Executable not found: '{name}'.\n"
            f"  - it is not on PATH and no explicit path is configured.\n"
            f"  - set its path in config.local.toml "
            f"(e.g. cmake_exe / ctest_exe / ninja_exe), or\n"
            f"  - run `{self._program} config` to see what the CLI resolved.")

    def run(self, cmd: list[str], cwd: Path,
            env: dict[str, str] | None = None) -> int:
        """Run *cmd*, letting the child inherit this process's stdout."""
        resolved = list(cmd)
        resolved[0] = self.resolve_exe(cmd[0], env)
        self._console.command(subprocess.list2cmdline(resolved))
        try:
            return subprocess.run(resolved, cwd=str(cwd), env=env).returncode
        except FileNotFoundError:
            self._not_found(cmd[0])
            return 1

    def run_drained(self, cmd: list[str], cwd: Path,
                    env: dict[str, str] | None = None) -> int:
        """Run *cmd* with its output piped here and re-emitted line by line.

        Draining the pipe ourselves is what keeps ctest's gtest_discover_tests
        step reliable on Windows: when ctest's stdout is an inherited, slowly
        drained pipe, the discovery child intermittently stalls and registers
        nothing, surfacing as "No tests were found".

        markup=False because child output carries literal "[file:line]" and
        "[[nodiscard]]" tags that Rich would otherwise parse as console markup
        and silently drop.
        """
        resolved = list(cmd)
        resolved[0] = self.resolve_exe(cmd[0], env)
        self._console.command(subprocess.list2cmdline(resolved))
        try:
            proc = subprocess.Popen(
                resolved, cwd=str(cwd), env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1)
        except FileNotFoundError:
            self._not_found(cmd[0])
            return 1
        assert proc.stdout is not None
        for line in proc.stdout:
            self._console.console.print(line.rstrip("\n"), markup=False,
                                        highlight=False, soft_wrap=True)
        return proc.wait()
