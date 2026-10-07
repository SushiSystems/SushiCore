# source_revision.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reads the commit a bundle is built from."""

from __future__ import annotations

import subprocess
from pathlib import Path

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
