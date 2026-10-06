# entry.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The entry point every Sushi CLI runs its Typer application through.

A console script names a ``main`` function that calls :func:`run`, so a failure the user
can act on leaves one line and exit code 1 on every CLI, and a defect stays a traceback.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Callable, NoReturn, Sequence

from .errors import SushiCoreError

if TYPE_CHECKING:
    import typer

K_EXIT_FAILURE = 1


def _report(program: str, report: Callable[[str], None], message: str) -> None:
    """Hands the message to the CLI's reporter, or to stderr when the reporter fails too."""
    try:
        report(message)
    except SushiCoreError:
        print(f"{program}: {message}", file=sys.stderr)


def run(
    app: "typer.Typer",
    report: Callable[[str], None],
    *,
    argv: Sequence[str] | None = None,
) -> NoReturn:
    """Runs a Typer application and exits; a sushicore failure becomes one line and exit 1.

    Args:
        app: The application to run.
        report: Prints one error line the way the CLI prints errors. It must look the printer
            up when called, e.g. ``lambda message: console.error(message)``: a console built
            from the same broken file fails on attribute access, before this function runs.
        argv: The arguments to parse; the process's own when None.
    """
    try:
        app(args=None if argv is None else list(argv))
    except SushiCoreError as error:
        _report(app.info.name or "cli", report, str(error))
        raise SystemExit(K_EXIT_FAILURE) from error
    raise SystemExit(0)
