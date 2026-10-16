# git_client.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Clones one tag of a repository and reads a checkout's HEAD through git."""

from __future__ import annotations

import logging
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from .packages.base import run

_log = logging.getLogger(__name__)


class IGitClient(ABC):
    """The two git operations fetching a pinned Sushi library needs."""

    @abstractmethod
    def clone_tag(self, url: str, tag: str, destination: Path, dry_run: bool) -> bool:
        """Clone only *tag* of *url* into *destination*, shallow; report success."""

    @abstractmethod
    def head(self, checkout: Path) -> str:
        """Return the commit *checkout*'s HEAD points at, or '' when git cannot say."""


class GitClient(IGitClient):
    """Runs the git on PATH."""

    def clone_tag(self, url: str, tag: str, destination: Path, dry_run: bool) -> bool:
        """Run ``git clone --depth 1 --branch <tag> --single-branch``; report success."""
        command = ["git", "clone", "--depth", "1", "--branch", tag, "--single-branch",
                   url, str(destination)]
        return run(command, dry_run, check=True) == 0

    def head(self, checkout: Path) -> str:
        """Run ``git rev-parse HEAD`` in *checkout*; return '' when it fails."""
        try:
            result = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"],
                                    capture_output=True, text=True)
        except OSError as exc:
            _log.warning("git could not run in %s: %s", checkout, exc)
            return ""
        if result.returncode != 0:
            _log.warning("git rev-parse HEAD failed in %s: %s", checkout, result.stderr.strip())
            return ""
        return result.stdout.strip().lower()
