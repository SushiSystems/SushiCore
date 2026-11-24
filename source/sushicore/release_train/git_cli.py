# git_cli.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The git operations of the train, through the git command."""

from __future__ import annotations

from pathlib import Path
from typing import final

from ..proc import CommandRunner
from .errors import ReleaseTrainError
from .version import Version, K_PATTERN


@final
class GitCli:
    """Runs git in a repository and raises ReleaseTrainError when a command fails."""

    def __init__(self, runner: CommandRunner) -> None:
        self._runner = runner

    def _git(self, repo: Path, *arguments: str) -> str:
        code, out, err = self._runner.capture(["git", *arguments], cwd=repo)
        if code != 0:
            raise ReleaseTrainError(f"{repo.name}: git {' '.join(arguments)} failed: {(err or out).strip()}")
        return out

    def is_clean(self, repo: Path) -> bool:
        return self._git(repo, "status", "--porcelain").strip() == ""

    def head(self, repo: Path) -> str:
        return self._git(repo, "rev-parse", "HEAD").strip()

    def latest_release(self, repo: Path) -> Version:
        tags = [line.strip() for line in self._git(repo, "tag", "--list", "v*").splitlines()]
        versions = [Version.parse(tag) for tag in tags if K_PATTERN.match(tag)]
        if not versions:
            raise ReleaseTrainError(f"{repo.name}: no vX.Y.Z tag")
        return max(versions)

    def last_release_files(self, repo: Path) -> list[Path]:
        commit = self._git(repo, "log", "-1", "--format=%H", "--grep=^chore(release): v").strip()
        if not commit:
            raise ReleaseTrainError(f"{repo.name}: no chore(release) commit to learn the version files from")
        listed = self._git(repo, "show", "--name-only", "--format=", commit)
        return [Path(line.strip()) for line in listed.splitlines() if line.strip()]

    def commit_all(self, repo: Path, message: str) -> None:
        self._git(repo, "add", "-A")
        self._git(repo, "commit", "-q", "-m", message)

    def push(self, repo: Path, *refs: str) -> None:
        self._git(repo, "push", "-q", "origin", "HEAD", *refs)

    def tag(self, repo: Path, name: str, commit: str) -> None:
        self._git(repo, "tag", name, commit)
