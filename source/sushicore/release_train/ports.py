# ports.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The seams of the train to git, to the forge that runs CI and to the package index."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .version import Version


class IGit(Protocol):
    """The git operations the train needs on one repository."""

    def is_clean(self, repo: Path) -> bool:
        """Return whether *repo* has no change, staged or not."""

    def head(self, repo: Path) -> str:
        """Return the full SHA of HEAD."""

    def latest_release(self, repo: Path) -> Version:
        """Return the highest vX.Y.Z tag."""

    def last_release_files(self, repo: Path) -> list[Path]:
        """Return the paths, from the root, the last `chore(release)` commit changed."""

    def commit_all(self, repo: Path, message: str) -> None:
        """Stage every change and commit it with *message*, hooks included."""

    def push(self, repo: Path, *refs: str) -> None:
        """Push the current branch and each ref of *refs* to origin."""

    def tag(self, repo: Path, name: str, commit: str) -> None:
        """Make the lightweight tag *name* on *commit*."""


class IForge(Protocol):
    """The forge that runs a repository's workflows."""

    def ci_passed(self, repo: Path, commit: str) -> bool:
        """Wait for the CI workflow of *commit* and return whether it succeeded."""

    def release_passed(self, repo: Path, commit: str) -> bool:
        """Wait for the release workflow of *commit* and return whether it succeeded."""


class IPackageIndex(Protocol):
    """The index the CLIs are published to."""

    def wait_for(self, package: str, version: Version) -> bool:
        """Wait until *package* lists *version* and return whether it did before the deadline."""
