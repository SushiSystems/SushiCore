# __main__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Plans or runs a release train: `python -m sushicore.release_train`.

Usage: python -m sushicore.release_train plan WORKSPACE LIBRARY...
       python -m sushicore.release_train run WORKSPACE LIBRARY... [--part patch|minor|major]
"""

from __future__ import annotations

import datetime
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from ..errors import SushiCoreError
from ..files import DiskFiles
from ..quiet_runner import quiet_runner
from .gh_forge import GhForge
from .git_cli import GitCli
from .pypi_index import PyPiIndex
from .release_train import ReleaseTrain

K_PROGRAM = "python -m sushicore.release_train"
K_EXIT_FAILURE = 1


def _say(line: str) -> None:
    """Writes one line of a result to standard output."""
    sys.stdout.write(f"{line}\n")


def _train(workspace: Path) -> ReleaseTrain:
    """Return the train of *workspace* over git, GitHub and PyPI."""
    runner = quiet_runner()
    return ReleaseTrain(workspace, DiskFiles(), GitCli(runner), GhForge(runner, time.sleep), PyPiIndex(time.sleep),
                        _say, datetime.date.today().isoformat())


def main(argv: Sequence[str] | None = None) -> int:
    """Runs one command and returns its exit code."""
    import typer

    app = typer.Typer(name=K_PROGRAM, no_args_is_help=True, add_completion=False)

    @app.command("plan", epilog=f"{K_PROGRAM} plan .. sushilog")
    def plan(workspace: Path = typer.Argument(..., help="The folder that holds the libraries side by side."),
             libraries: list[str] = typer.Argument(..., help="The libraries that changed.")) -> None:
        """Print the libraries a release of LIBRARIES takes, in the order the train walks them."""
        for name in _train(workspace).plan(libraries):
            _say(name)

    @app.command("run", epilog=f"{K_PROGRAM} run .. sushilog --part patch")
    def run(workspace: Path = typer.Argument(..., help="The folder that holds the libraries side by side."),
            libraries: list[str] = typer.Argument(..., help="The libraries that changed."),
            part: str = typer.Option("patch", help="The part of their version to raise: patch, minor or major.")) -> None:
        """Release LIBRARIES and every library that pins them, each after what it pins."""
        _train(workspace).run(libraries, part)

    try:
        app(list(sys.argv[1:] if argv is None else argv), prog_name=K_PROGRAM, standalone_mode=False)
    except SushiCoreError as error:
        sys.stderr.write(f"{K_PROGRAM}: {error}\n")
        return K_EXIT_FAILURE
    except typer.Exit as stop:
        return stop.exit_code
    return 0


if __name__ == "__main__":
    sys.exit(main())
