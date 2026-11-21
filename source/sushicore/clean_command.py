# clean_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The `clean` command every CLI declares: it lists build trees and removes them only on `--sure`.

The reasoning is in docs/architecture/OVERVIEW.md, section `clean_command`. This module takes no
`from __future__ import annotations`: Typer reads the command's annotations when it is declared.
"""

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Protocol

from .build_tree import tree_dir

if TYPE_CHECKING:
    import typer

K_SURE_FLAG = "--sure"
K_REFUSED_EXIT_CODE = 2


class CleanConsole(Protocol):
    """The console lines the command prints."""

    def header(self, title: str) -> None:
        """Prints a section header."""

    def info(self, text: str) -> None:
        """Prints an information line."""

    def error(self, text: str) -> None:
        """Prints an error line."""


class CleanDriver(Protocol):
    """What removes one build tree."""

    def clean_tree(self, build_dir: Path) -> None:
        """Removes *build_dir*, or raises when something of it remains."""


class CleanTarget(Protocol):
    """What the command acts on: a checkout, where it prints and what removes a tree."""

    root: Path
    console: CleanConsole
    driver: CleanDriver


def select_trees(
    root: Path, names: Mapping[Optional[str], str], build_types: Sequence[str], *,
    types: Sequence[str] = (), sanitizers: Sequence[str] = (),
) -> list[Path]:
    """Returns the existing build trees under *root* that the filters select.

    A tree is `build/<name>-<type>`. *types* picks build types of the plain tree, *sanitizers*
    picks the trees of those sanitizers in every build type or in *types*, and no filter picks
    every tree.

    Args:
        names: The tree name of each sanitizer, ``None`` for the plain tree.
        build_types: Every build type the CLI builds.
        types: Build types to select; every type when empty.
        sanitizers: Sanitizers to select; the plain tree when only *types* is given, every tree
            when neither is.
    """
    keys = list(sanitizers) if sanitizers else ([None] if types else list(names))
    chosen = [build_type.lower() for build_type in types] or [t.lower() for t in build_types]
    found: list[Path] = []
    for key in keys:
        for build_type in chosen:
            tree = tree_dir(root, names[key], build_type)
            if tree.is_dir() and tree not in found:
                found.append(tree)
    return found


def clean_trees(target: CleanTarget, trees: Sequence[Path], *, sure: bool) -> int:
    """Lists *trees* and removes them when *sure*; returns the exit code.

    Without *sure* nothing is removed and the code is `K_REFUSED_EXIT_CODE`, so a script that
    expected the trees gone sees that they are not.
    """
    console = target.console
    if not trees:
        console.info("No build tree to remove.")
        return 0
    for tree in trees:
        console.info(f"  {tree}")
    if not sure:
        console.error(f"Nothing was removed. Add {K_SURE_FLAG} to remove the trees above.")
        return K_REFUSED_EXIT_CODE
    for tree in trees:
        target.driver.clean_tree(tree)
    return 0


def register_clean_command(
    app: "typer.Typer", resolve: Callable[["typer.Context"], CleanTarget], *,
    program: str, panel: str, names: Mapping[Optional[str], str], build_types: Sequence[str],
) -> None:
    """Adds ``clean`` to *app*.

    Args:
        app: The application to add the command to.
        resolve: Returns what the command acts on, from the command's context.
        program: The command the user types, for the examples.
        panel: The help panel the command is listed under.
        names: The tree name of each sanitizer, ``None`` for the plain tree.
        build_types: Every build type the CLI builds, such as ``debug`` and ``release``.
    """
    import click
    import typer

    sanitizers = [key for key in names if key is not None]

    @app.command(
        "clean",
        rich_help_panel=panel,
        epilog=f"{program} clean  # List every build tree, remove none\n"
               f"{program} clean {K_SURE_FLAG}  # Remove every build tree\n"
               f"{program} clean --type debug {K_SURE_FLAG}  # Remove the debug tree only",
    )
    def clean(
        ctx: typer.Context,
        type: Optional[list[str]] = typer.Option(
            None, "--type", "-t",
            click_type=click.Choice(list(build_types), case_sensitive=False),
            help="Select the tree of this build type, repeatable. None selects every type."),
        sanitize: Optional[list[str]] = typer.Option(
            None, "--sanitize", hidden=not sanitizers,
            click_type=click.Choice(sanitizers, case_sensitive=False),
            help="Select the trees of this sanitizer, repeatable."),
        sure: bool = typer.Option(
            False, K_SURE_FLAG, help="Remove the trees. Without it the command only lists them."),
    ) -> None:
        """List the build trees a filter selects, and remove them only with --sure."""
        target = resolve(ctx)
        target.console.header("Project Clean")
        trees = select_trees(
            target.root, names, build_types, types=type or (), sanitizers=sanitize or ())
        raise typer.Exit(clean_trees(target, trees, sure=sure))
