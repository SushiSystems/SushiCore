# verification.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads the verification stamp and the commits after it from git.

The judgement of which IDs those commits leave unverified is `unverified.py`.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

from .unverified import unverified_ids

K_STAMP_PATH = ("sushicore", "verified")
K_LOG_SEPARATOR = "%x00"
K_SEPARATOR = "\x00"


def run_git(root: Path, *arguments: str) -> str | None:
    """Runs git in *root* and returns its output, or None when it fails or is not installed."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
    except OSError:
        return None
    return completed.stdout if completed.returncode == 0 else None


class GitVerification:
    """Reads which IDs are unverified in a checkout: those named after the stamped commit."""

    def __init__(self, git: Callable[..., str | None] = run_git) -> None:
        """Takes the function that runs git, so a test can replace it."""
        self._git = git

    def unverified(self, root: Path) -> frozenset[str] | None:
        """Returns the IDs named after the stamp, or None when the checkout has no stamp."""
        git_dir = self._git(root, "rev-parse", "--git-dir")
        if git_dir is None:
            return None
        stamp_file = (root / git_dir.strip()).joinpath(*K_STAMP_PATH)
        if not stamp_file.is_file():
            return None
        stamp = stamp_file.read_text(encoding="utf-8").strip()
        log = self._git(root, "log", f"--format=%B{K_LOG_SEPARATOR}", f"{stamp}..HEAD")
        if log is None:
            return None
        return unverified_ids(log.split(K_SEPARATOR))
