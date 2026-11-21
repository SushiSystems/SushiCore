# clean_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The `clean` command every CLI declares: it lists build trees and removes them only on `--yes`.

The reasoning is in docs/architecture/OVERVIEW.md, section `clean_command`. This module takes no
`from __future__ import annotations`: Typer reads the command's annotations when it is declared.
"""

import os
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Protocol

from .build_tree import tree_dir

if TYPE_CHECKING:
    import typer

K_YES_FLAG = "--yes"
K_YES_SHORT_FLAG = "-y"
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
    type_trees: Optional[Mapping[str, str]] = None,
) -> list[Path]:
    """Returns the existing build trees under *root* that the filters select.

    A tree is `build/<name>-<type>`. *types* picks build types of the plain tree, *sanitizers*
    picks the trees of those sanitizers in every build type or in *types*, and no filter picks
    every tree. A type of *type_trees* names one folder of `build/` outright.

    Args:
        names: The tree name of each sanitizer, ``None`` for the plain tree.
        build_types: Every build type of the plain tree and the sanitizer trees.
        types: Types to select; every tree when empty and no sanitizer is given.
        sanitizers: Sanitizers to select; the plain tree when only *types* is given.
        type_trees: The folder of `build/` that a type names outright, such as an ASan type that
            builds in `asan-release`.
    """
    type_trees = type_trees or {}
    lowered = [name.lower() for name in types]
    candidates: list[Path] = []
    if sanitizers:
        chosen = [name for name in lowered if name in build_types] or list(build_types)
        candidates = [tree_dir(root, names[key], build_type)
                      for key in sanitizers for build_type in chosen]
    elif lowered:
        for name in lowered:
            candidates.append(root / "build" / type_trees[name] if name in type_trees
                              else tree_dir(root, names[None], name))
    else:
        candidates = [tree_dir(root, tree, build_type)
                      for tree in names.values() for build_type in build_types]
        candidates += [root / "build" / folder for folder in type_trees.values()]
    found: list[Path] = []
    for tree in candidates:
        if tree.is_dir() and tree not in found:
            found.append(tree)
    return found


def clean_trees(target: CleanTarget, trees: Sequence[Path], *, yes: bool) -> int:
    """Lists *trees* and removes them when *yes*; returns the exit code.

    Without *yes* nothing is removed and the code is `K_REFUSED_EXIT_CODE`, so a script that
    expected the trees gone sees that they are not.
    """
    console = target.console
    if not trees:
        console.info("No build tree to remove.")
        return 0
    console.info("Removing these build trees:" if yes else "These build trees would be removed:")
    for tree in trees:
        console.info(f"  {tree}  ({_size_text(tree_size(tree))})")
    if not yes:
        console.error(f"Nothing was removed. Add {K_YES_FLAG} to remove them.")
        return K_REFUSED_EXIT_CODE
    for tree in trees:
        target.driver.clean_tree(tree)
    return 0


def tree_size(tree: Path) -> int:
    """Returns the bytes of the files under *tree*; a file that cannot be read counts as none."""
    total = 0
    pending = [tree]
    while pending:
        try:
            with os.scandir(pending.pop()) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(Path(entry.path))
                    else:
                        total += entry.stat(follow_symlinks=False).st_size
        except OSError:
            continue
    return total


def _size_text(size: int) -> str:
    """Returns *size* in the largest binary unit that keeps it above one, such as ``2.3 GiB``."""
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TiB"


def register_clean_command(
    app: "typer.Typer", resolve: Callable[["typer.Context"], CleanTarget], *,
    program: str, panel: str, names: Mapping[Optional[str], str], build_types: Sequence[str],
    type_trees: Optional[Mapping[str, str]] = None,
) -> None:
    """Adds ``clean`` to *app*.

    Args:
        app: The application to add the command to.
        resolve: Returns what the command acts on, from the command's context.
        program: The command the user types, for the examples.
        panel: The help panel the command is listed under.
        names: The tree name of each sanitizer, ``None`` for the plain tree.
        build_types: Every build type the CLI builds, such as ``debug`` and ``release``.
        type_trees: The types that name a folder of `build/` outright, as ``asan`` names
            ``asan-release`` for a CLI whose ``--type`` also picks a sanitizer.
    """
    import enum

    import typer

    type_trees = dict(type_trees or {})
    sanitizers = [key for key in names if key is not None]
    # Typer offers an enum as a choice, so no click import is needed: `--label` does the same.
    type_choice = enum.Enum(
        "BuildTypeChoice", {name: name for name in [*build_types, *type_trees]}, type=str)
    sanitizer_choice = enum.Enum("SanitizerChoice", {name: name for name in sanitizers}, type=str)

    @app.command(
        "clean",
        rich_help_panel=panel,
        epilog=f"{program} clean  # List every build tree, remove none\n"
               f"{program} clean {K_YES_FLAG}  # Remove every build tree\n"
               f"{program} clean --type debug {K_YES_FLAG}  # Remove the debug tree only",
    )
    def clean(
        ctx: typer.Context,
        type: Optional[list[type_choice]] = typer.Option(
            None, "--type", "-t", case_sensitive=False,
            help="Select the tree of this type, repeatable. None selects every tree."),
        sanitize: Optional[list[sanitizer_choice]] = typer.Option(
            None, "--sanitize", case_sensitive=False, hidden=not sanitizers,
            help="Select the trees of this sanitizer, repeatable."),
        yes: bool = typer.Option(
            False, K_YES_FLAG, K_YES_SHORT_FLAG,
            help="Remove the trees. Without it the command only lists them."),
    ) -> None:
        """List the build trees a filter selects, and remove them only with --yes."""
        target = resolve(ctx)
        target.console.header("Project Clean")
        trees = select_trees(
            target.root, names, build_types, types=[choice.value for choice in type or ()],
            sanitizers=[choice.value for choice in sanitize or ()], type_trees=type_trees)
        raise typer.Exit(clean_trees(target, trees, yes=yes))
