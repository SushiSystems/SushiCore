# run_options.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The options of a `run` command that picks a program, declared once for every CLI.

The reasoning is in docs/architecture/OVERVIEW.md, section `run_options`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import typer

    from .aliases import AliasTable

K_PICK_FLAG = "--pick"
K_LIST_ALL_FLAG = "--all"


def pick_option() -> "typer.models.OptionInfo":
    """Returns the default of the ``--pick`` parameter, a ``bool``."""
    import typer

    return typer.Option(False, K_PICK_FLAG, help="Interactively pick an example.")


def list_all_option() -> "typer.models.OptionInfo":
    """Returns the default of the ``--all`` parameter, a ``bool``."""
    import typer

    return typer.Option(
        False, K_LIST_ALL_FLAG, help="With --pick, also list the test and benchmark programs.")


def old_pick_option(
    table: "AliasTable", old: str, *names: str,
) -> "typer.models.OptionInfo":
    """Returns the default of a hidden old spelling of ``--pick``, a ``bool``.

    Args:
        table: The CLI's alias table; the row *old* must be in it.
        old: The full old spelling, a key of *table*, such as ``sr run --sort``.
        names: The flag names the old option answers to; ``--sort`` when none is given.
    """
    import typer

    return typer.Option(
        False, *(names or ("--sort",)), hidden=True, callback=table.flag_announcer(old),
        help="The old spelling of --pick.")
