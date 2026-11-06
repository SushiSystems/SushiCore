# source_revision.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads the commit a bundle is built from."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import final

from .errors import ReleaseError


def read_head_commit(repository_root: Path) -> str:
    """Returns the full hash of the commit checked out in *repository_root*.

    Raises:
        ReleaseError: git cannot be run, or the folder is not a checkout.
    """
    try:
        done = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root, capture_output=True, text=True, check=False,
        )
    except OSError as error:
        raise ReleaseError(
            "git could not be run, and a bundle records the commit it was built from."
        ) from error
    if done.returncode != 0:
        raise ReleaseError(f"{repository_root} is not a git checkout: {done.stderr.strip()}")
    return done.stdout.strip()


@final
class FixedCommit:
    """A commit reader that returns one hash for every folder, for a run with no git."""

    def __init__(self, commit: str) -> None:
        """Stores the hash every call returns."""
        self._commit = commit

    def __call__(self, repository_root: Path) -> str:
        """Returns the stored hash."""
        return self._commit
