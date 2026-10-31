# options.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Declares the options every ``test`` command shares, so a CLI that keeps its own command spells them alike."""

from __future__ import annotations


def label_option() -> "typer.models.OptionInfo":
    """Returns the default of the ``--label`` parameter, a ``List[TestLabel]`` that may be None."""
    import typer

    return typer.Option(
        None, "--label", "-l", case_sensitive=False,
        help="Size label to run, repeatable: small, medium, large or quarantined. "
             "Default: small and medium; large needs --filter or --all.")


def filter_option() -> "typer.models.OptionInfo":
    """Returns the default of the ``--filter`` parameter, an ``Optional[str]``."""
    import typer

    return typer.Option(None, "--filter", "-f", metavar="REGEX",
                        help="ctest -R regex over 'Suite.Case' test names.")


def repeat_option() -> "typer.models.OptionInfo":
    """Returns the default of the ``--repeat`` parameter, an ``int``."""
    import typer

    return typer.Option(0, "--repeat", "-r", min=0, metavar="N",
                        help="Re-run each test up to N times, stopping on the first failure.")


def jobs_option() -> "typer.models.OptionInfo":
    """Returns the default of the ``--jobs`` parameter, an ``Optional[int]``."""
    import typer

    return typer.Option(None, "--jobs", "-j", min=1, metavar="N",
                        help="Run up to N tests concurrently (ctest --parallel).")


def all_option() -> "typer.models.OptionInfo":
    """Returns the default of the ``--all`` parameter, a ``bool``."""
    import typer

    return typer.Option(False, "--all", help="Run every size, the large tests included.")
