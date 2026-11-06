# console_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A console that records every call instead of printing, for tests of code that prints.

It satisfies the console surface of `proc.ConsoleLike`, `testing.module_tests.TestConsole`
and `provision.package_install._Console`, and touches no terminal.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from typing import ContextManager, NamedTuple, Sequence


class ConsoleCall(NamedTuple):
    """One recorded call: the method name and the positional arguments it was given."""

    kind: str
    args: tuple[object, ...]

    @property
    def text(self) -> str:
        """Return the first argument as text, or an empty string when the call had none."""
        return str(self.args[0]) if self.args else ""


@dataclass(frozen=True, slots=True)
class PrintedOutput:
    """One ``console.print`` call of the Rich console: its objects and its keyword options."""

    objects: tuple[object, ...]
    options: dict[str, object] = field(default_factory=dict)

    @property
    def text(self) -> str:
        """Return the first printed object as text, or an empty string when none was given."""
        return str(self.objects[0]) if self.objects else ""


class RecordingRichConsole:
    """Stands in for the Rich console behind ``console``; records ``print`` and ``status``."""

    def __init__(self, calls: list[ConsoleCall]) -> None:
        """Record into *calls*, the owning :class:`RecordingConsole`'s list."""
        self._calls = calls
        self.printed: list[PrintedOutput] = []

    def print(self, *objects: object, **options: object) -> None:
        """Record the objects printed and the options they were printed with."""
        self.printed.append(PrintedOutput(objects, dict(options)))
        self._calls.append(ConsoleCall("console.print", objects))

    def status(self, *args: object, **_options: object) -> ContextManager[None]:
        """Record the status line and return a context that does nothing."""
        self._calls.append(ConsoleCall("console.status", args))
        return contextlib.nullcontext()


class RecordingConsole:
    """Records every console call, in order, and answers prompts from a fixed answer.

    Args:
        machine: What ``is_machine`` reports.
        answer: What ``prompt`` returns; ``None`` returns the prompt's own default.
    """

    def __init__(self, *, machine: bool = False, answer: str | None = None) -> None:
        """Start with no recorded calls."""
        self.calls: list[ConsoleCall] = []
        self.console = RecordingRichConsole(self.calls)
        self._machine = machine
        self._answer = answer

    def info(self, text: str) -> None:
        """Record an information line."""
        self._record("info", text)

    def success(self, text: str) -> None:
        """Record a success line."""
        self._record("success", text)

    def warn(self, text: str) -> None:
        """Record a warning line."""
        self._record("warn", text)

    def error(self, text: str) -> None:
        """Record an error line."""
        self._record("error", text)

    def command(self, text: str) -> None:
        """Record a command line."""
        self._record("command", text)

    def header(self, title: str) -> None:
        """Record a section header."""
        self._record("header", title)

    def fail_panel(self, title: str, body: str) -> None:
        """Record a failure panel."""
        self._record("fail_panel", title, body)

    def table(self, columns: Sequence[str], rows: Sequence[Sequence[str]], title: str = "",
              *, group_by: str | None = None) -> None:
        """Record a table with its title and the column it groups by."""
        self._record("table", columns, rows, title, group_by)

    def progress(self, label: str, index: int, count: int,
                 fraction: float | None = None) -> None:
        """Record a progress step."""
        self._record("progress", label, index, count, fraction)

    def result(self, ok: bool, payload: dict | None = None) -> None:
        """Record the final machine-readable result."""
        self._record("result", ok, payload)

    def prompt(self, message: str, default: str | None = None) -> str:
        """Record the question and return the fixed answer, or *default* when none is set."""
        self._record("prompt", message, default)
        if self._answer is not None:
            return self._answer
        return default or ""

    def is_machine(self) -> bool:
        """Return the machine-mode flag this console was built with."""
        return self._machine

    def texts(self, kind: str) -> list[str]:
        """Return the text of every call of *kind*, in call order."""
        return [call.text for call in self.calls if call.kind == kind]

    def has_call(self, kind: str) -> bool:
        """Return whether a call of *kind* was recorded."""
        return any(call.kind == kind for call in self.calls)

    def _record(self, kind: str, *args: object) -> None:
        """Append one call to the record."""
        self.calls.append(ConsoleCall(kind, args))
