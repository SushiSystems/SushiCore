# verification.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads the verification stamp and the commits after it, with their paths, from git.

The judgement of which IDs those commits leave unverified is `unverified.py`.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import final

from ..proc import CommandRunner
from ..quiet_runner import quiet_runner
from .unverified import Commit, unverified_ids

K_STAMP_PATH = ("sushicore", "verified")
K_LOG_FORMAT = "--format=%x01%B%x02"
K_COMMIT_MARK = "\x01"
K_MESSAGE_END = "\x02"


def parse_log(log: str) -> list[Commit]:
    """Returns the commits of a `git log --name-only` run with the format `K_LOG_FORMAT`."""
    commits = []
    for record in log.split(K_COMMIT_MARK)[1:]:
        message, _, listing = record.partition(K_MESSAGE_END)
        commits.append(Commit(message, tuple(line.strip() for line in listing.splitlines() if line.strip())))
    return commits


def run_git(root: Path, *arguments: str, runner: CommandRunner | None = None) -> str | None:
    """Runs git in *root* and returns its output, or None when it fails or is not installed.

    *runner* spawns git; the real one when None.
    """
    try:
        code, stdout, _ = (runner if runner is not None else quiet_runner()).capture(
            ["git", "-C", str(root), *arguments], encoding="utf-8")
    except OSError:
        return None
    return stdout if code == 0 else None


@final
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
        log = self._git(root, "log", "--name-only", K_LOG_FORMAT, f"{stamp}..HEAD")
        if log is None:
            return None
        return unverified_ids(parse_log(log))
