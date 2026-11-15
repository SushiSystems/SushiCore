# __main__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Runs `sync` and `check` of the shared tools: `python -m sushicore.shared_tools`.

Usage: python -m sushicore.shared_tools sync ROOT --tag vX.Y.Z [--from PATH] [--force] [--keep PATH] [--dry-run]
       python -m sushicore.shared_tools check ROOT
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

from ..errors import SushiCoreError
from .commands import register_shared_tools_commands

K_PROGRAM = "python -m sushicore.shared_tools"
K_EXIT_FAILURE = 1


def _complain(line: str) -> None:
    """Writes one line of a refusal to standard error."""
    sys.stderr.write(f"{line}\n")


def main(argv: Sequence[str] | None = None) -> int:
    """Runs one command and returns its exit code."""
    import typer

    app = typer.Typer(name=K_PROGRAM, no_args_is_help=True, add_completion=False)
    register_shared_tools_commands(app, program=K_PROGRAM, complain=_complain)
    try:
        code = app(list(sys.argv[1:] if argv is None else argv), prog_name=K_PROGRAM, standalone_mode=False)
    except SushiCoreError as error:
        _complain(f"{K_PROGRAM}: {error}")
        return K_EXIT_FAILURE
    except typer.Exit as stop:
        return stop.exit_code
    except Exception as error:
        if not (hasattr(error, "show") and hasattr(error, "exit_code")):
            raise
        error.show()
        return error.exit_code
    return code if isinstance(code, int) else 0


if __name__ == "__main__":
    sys.exit(main())
