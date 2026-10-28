# __main__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Runs the `design` group for a repository that has no CLI of its own.

Usage: python -m sushicore.design [--root DIR] <command> ...
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from ..errors import SushiCoreError
from .commands import register_design_commands

K_PROGRAM = "python -m sushicore.design"
K_EXIT_FAILURE = 1


def main(argv: Sequence[str] | None = None) -> int:
    """Runs one command of the group on the repository at --root, or the current folder."""
    import typer

    arguments = list(sys.argv[1:] if argv is None else argv)
    root = Path.cwd()
    if len(arguments) >= 2 and arguments[0] == "--root":
        root = Path(arguments[1])
        arguments = arguments[2:]
    app = typer.Typer(name=K_PROGRAM, no_args_is_help=True, add_completion=False)
    register_design_commands(app, program=K_PROGRAM, panel="Documentation", project_root=lambda: root.resolve())
    try:
        code = app(["design", *arguments], prog_name=K_PROGRAM, standalone_mode=False)
    except SushiCoreError as error:
        print(f"{K_PROGRAM}: {error}", file=sys.stderr)
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
