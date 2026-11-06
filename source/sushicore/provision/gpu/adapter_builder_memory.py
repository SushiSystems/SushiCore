# adapter_builder_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A command runner for the adapter builder that records each command and starts no process."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


class InMemoryCommandRunner:
    """Records every command and answers 0, except for the one it is told to fail.

    Args:
        fail_on: A word; a command whose argv holds it exits 1.
        missing: Whether every command raises :class:`FileNotFoundError`, as an
            executable that is on no PATH does.
    """

    def __init__(self, *, fail_on: str | None = None, missing: bool = False) -> None:
        """Start with no recorded commands."""
        self._fail_on = fail_on
        self._missing = missing
        self.calls: list[list[str]] = []

    def run(self, argv: list[str], cwd: Path | None,
            env: dict[str, str] | None) -> int:
        """Record *argv*, then raise, fail or succeed as configured."""
        self.calls.append(list(argv))
        if self._missing:
            raise FileNotFoundError(argv[0])
        if self._fail_on is not None and self._fail_on in argv:
            return 1
        return 0


class InMemoryAdapterBuilder:
    """Records the vendor of every build it is asked for and answers a fixed outcome per vendor.

    Args:
        outcomes: Whether the build of each vendor succeeds; a vendor left out succeeds.

    Attributes:
        built: The vendor of each build, in the order they were asked for.
    """

    def __init__(self, outcomes: Mapping[str, bool] | None = None) -> None:
        """Start with no recorded builds."""
        self._outcomes = dict(outcomes or {})
        self.built: list[str] = []

    def build(self, spec: Any, install: Any, toolchain_root: Path, commit: str,
              dry_run: bool) -> bool:
        """Record the vendor of *spec* and return its outcome."""
        self.built.append(spec.vendor)
        return self._outcomes.get(spec.vendor, True)
