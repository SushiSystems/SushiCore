# commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Registers the shared ``test`` command that every Sushi CLI with CTest tests offers."""

from __future__ import annotations

from typing import List, Optional

from .labels import TestLabel, select_labels
from .module_tests import ModuleTests
from .options import all_option, filter_option, jobs_option, label_option, repeat_option
from .session import run_tests


def register_test_command(app: "typer.Typer", module: ModuleTests) -> None:
    """Add ``test`` to *app*: run the tests of the build tree by size label and print the budget line.

    Args:
        app: The CLI's Typer application.
        module: What the CLI hands the command: its tree, its CTest call and its checkout.
    """
    import typer

    program = module.profile.program
    sanitizers = ", ".join(module.sanitized.names) if module.sanitized else ""
    epilog = "\n".join((
        f"{program} test  # small and medium",
        f"{program} test --label small -f 'RectTest'",
        f"{program} test --label medium --repeat 3",
        f"{program} test --label large -f 'Gpu'  # Needs real hardware",
        f"{program} test --all  # Every size; the owner's machine runs this",
    ))

    @app.command("test", rich_help_panel=module.panel, epilog=epilog)
    def test(
        label: Optional[List[TestLabel]] = label_option(),
        filter: Optional[str] = filter_option(),
        repeat: int = repeat_option(),
        jobs: Optional[int] = jobs_option(),
        all_sizes: bool = all_option(),
        sanitize: Optional[str] = typer.Option(
            None, "--sanitize", metavar="NAME", hidden=module.sanitized is None,
            help="Build the tree of this sanitizer first and test it: " + sanitizers + "."),
        own: bool = typer.Option(
            False, "--cli", hidden=module.cli_tests is None,
            help="Run the pytest suite of this CLI instead of the CTest tests."),
    ) -> None:
        """Run the tests of the build tree by size label, then print the budget line.

        --sanitize builds the tree of a sanitizer first. --cli runs the pytest suite of this CLI.
        """
        selection = select_labels(label, every_size=all_sizes)
        raise typer.Exit(run_tests(module, selection, name_filter=filter, repeat=repeat,
                                   jobs=jobs, every_size=all_sizes, sanitizer=sanitize, own_tests=own))
