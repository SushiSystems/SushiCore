# commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The `sync` and `check` commands of `python -m sushicore.shared_tools`.

The behaviour of each command is in `docs/reference/SHARED_TOOLS.md`.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .checkout_finder import find_checkout
from .errors import (
    CheckoutNotFoundError,
    LocalEditsError,
    NoLockError,
    SharedToolsError,
    TagNotFoundError,
)
from .git_reader import GitReader
from .lock_file import read_lock
from .sync_service import SharedToolsSync

if TYPE_CHECKING:
    import typer

K_EXIT_FINDINGS = 1
K_EXIT_USAGE = 2
K_USAGE_ERRORS = (CheckoutNotFoundError, TagNotFoundError, NoLockError)


def register_shared_tools_commands(
    app: "typer.Typer",
    *,
    program: str,
    report: Callable[[str], None] = print,
    complain: Callable[[str], None] = print,
) -> None:
    """Adds `sync` and `check` to *app*.

    Args:
        app: The application to add the commands to.
        program: The command the user types, for the examples.
        report: Prints one line of a result.
        complain: Prints one line of a refusal.
    """
    import typer

    def fail(error: SharedToolsError) -> typer.Exit:
        """Prints the error and returns the exit that carries its code."""
        complain(f"{program}: {error}")
        return typer.Exit(K_EXIT_USAGE if isinstance(error, K_USAGE_ERRORS) else K_EXIT_FINDINGS)

    @app.command("sync", epilog=f"{program} sync . --tag v0.14.1\n{program} sync . --tag v0.14.1 --dry-run")
    def sync(
        root: Path = typer.Argument(..., help="The repository to bring up to the tag."),
        tag: str = typer.Option(..., "--tag", help="The SushiCore release tag to read, such as v0.14.1."),
        source: Optional[Path] = typer.Option(None, "--from", help="A SushiCore checkout; else the sibling or the fetched copy."),
        force: bool = typer.Option(False, "--force", help="Overwrite a shared file that holds a local edit."),
        keep: list[str] = typer.Option([], "--keep", metavar="PATH", help="Leave this shared file as the repository holds it; repeatable."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Write nothing; list what a sync would write."),
    ) -> None:
        """Copy the shared tools of a SushiCore tag into a repository and record them in tools/shared_tools.lock."""
        if not root.is_dir():
            complain(f"{program}: {root} is not a directory")
            raise typer.Exit(K_EXIT_USAGE)
        try:
            reader = GitReader(find_checkout(root, tag, source))
            result = SharedToolsSync(reader, root, tag, keep=keep, force=force, dry_run=dry_run).run()
        except LocalEditsError as error:
            for path in error.files:
                complain(f"{path}: a local edit; move it upstream or pass --force")
            raise typer.Exit(K_EXIT_FINDINGS) from error
        except SharedToolsError as error:
            raise fail(error) from error
        for path in result.dropped:
            report(f"{path}: dropped upstream; remove it")
        for name, value in result.missing_settings.items():
            known = f"{name} = {value}" if value is not None else f"{name}, which SushiCore does not define"
            report(f"tools/settings.py: lacks {known}")
        verb = "would write" if dry_run else "written"
        for path in result.written:
            report(f"{path}: {verb}")

    @app.command("check", epilog=f"{program} check .")
    def check(root: Path = typer.Argument(..., help="The repository to check against its lock.")) -> None:
        """Name each shared file that is missing or differs from tools/shared_tools.lock; exit 1 when any does."""
        try:
            lock = read_lock(root)
        except SharedToolsError as error:
            raise fail(error) from error
        differing = lock.differing(root)
        for path in differing:
            report(f"{path}: differs from the lock of {lock.tag}")
        if differing:
            raise typer.Exit(K_EXIT_FINDINGS)
