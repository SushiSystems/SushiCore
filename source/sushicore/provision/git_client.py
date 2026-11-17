# git_client.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Clones one tag or one commit of a repository and reads a checkout's HEAD through git."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, final

from .default_console import console_or_default
from ..proc import CommandRunner
from .process_run import provision_runner

_log = logging.getLogger(__name__)


class IGitClient(ABC):
    """The git operations fetching a pinned library needs."""

    @abstractmethod
    def clone_tag(self, url: str, tag: str, destination: Path, dry_run: bool) -> bool:
        """Clone only *tag* of *url* into *destination*, shallow; report success."""

    @abstractmethod
    def checkout_commit(self, url: str, commit: str, destination: Path, dry_run: bool, *,
                        shallow: bool = True) -> bool:
        """Fetch only *commit* of *url* into *destination* and check it out detached; report success.

        The fetch names the full hash, so nothing a branch or tag moves to is ever read. The
        caller reads :meth:`head` afterwards to confirm the checkout.
        """

    @abstractmethod
    def head(self, checkout: Path) -> str:
        """Return the commit *checkout*'s HEAD points at, or '' when git cannot say."""


@final
class GitClient(IGitClient):
    """Runs the git on PATH, or the executable it was given.

    Args:
        git: The git executable; ``git`` on PATH by default.
        runner: Runs the clone drained and captures the HEAD read; the provision runner on
            *console* when ``None``.
        console: The console the clone's output is shown through.
    """

    def __init__(self, git: str = "git", runner: CommandRunner | None = None, *,
                 console: Any = None) -> None:
        """Store the executable and the runner."""
        console = console_or_default(console, "GitClient")
        self._git = git
        self._runner = runner or provision_runner(console)

    def clone_tag(self, url: str, tag: str, destination: Path, dry_run: bool) -> bool:
        """Run ``git clone --depth 1 --branch <tag> --single-branch``; report success."""
        command = [self._git, "clone", "--depth", "1", "--branch", tag, "--single-branch",
                   url, str(destination)]
        return self._runner.run_drained(command, None, dry_run=dry_run, check=True) == 0

    def checkout_commit(self, url: str, commit: str, destination: Path, dry_run: bool, *,
                        shallow: bool = True) -> bool:
        """Run ``git init``, ``remote add``, ``fetch`` of *commit* and ``checkout --detach``."""
        repo = [self._git, "-C", str(destination)]
        fetch = [*repo, "fetch", *(["--depth", "1"] if shallow else []), "origin", commit]
        steps = [
            [self._git, "init", str(destination)],
            [*repo, "remote", "add", "origin", url],
            fetch,
            [*repo, "checkout", "--detach", "FETCH_HEAD"],
        ]
        return all(self._runner.run_drained(step, None, dry_run=dry_run, check=True) == 0
                   for step in steps)

    def head(self, checkout: Path) -> str:
        """Run ``git rev-parse HEAD`` in *checkout*; return '' when it fails."""
        code, out, err = self._runner.capture([self._git, "-C", str(checkout), "rev-parse", "HEAD"])
        if code != 0:
            _log.warning("git rev-parse HEAD failed in %s: %s", checkout, err.strip())
            return ""
        return out.strip().lower()
