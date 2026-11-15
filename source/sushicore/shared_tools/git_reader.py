# git_reader.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads files, history and commits of a SushiCore checkout through git, never from its working tree."""

from __future__ import annotations

import io
import subprocess
import tarfile
from pathlib import Path

from .errors import SharedToolsError, TagNotFoundError


class GitReader:
    """Reads one git checkout; every read names the revision it wants."""

    def __init__(self, checkout: Path) -> None:
        """Stores the checkout to read."""
        self._checkout = checkout

    def commit(self, tag: str) -> str:
        """Returns the commit the tag names; raises TagNotFoundError when the checkout has no such tag."""
        done = self._run("rev-parse", "--verify", "--quiet", f"{tag}^{{commit}}")
        if done is None or not done.strip():
            raise TagNotFoundError(f"{self._checkout} holds no tag {tag}")
        return done.strip()

    def files(self, tag: str, *paths: str) -> list[str]:
        """Returns the files the tag holds under the given paths, in git's order."""
        listed = self._run("ls-tree", "-r", "--name-only", tag, "--", *paths)
        return [line for line in (listed or "").splitlines() if line]

    def show(self, tag: str, path: str) -> str | None:
        """Returns a file as the tag holds it with LF newlines, or None when the tag lacks it."""
        shown = self._run("show", f"{tag}:{path}")
        return None if shown is None else shown.replace("\r\n", "\n")

    def history(self, tag: str, path: str) -> list[str]:
        """Returns every text the file held in a commit reachable from the tag, newest first."""
        revisions = (self._run("log", "--format=%H", tag, "--", path) or "").split()
        texts = (self.show(revision, path) for revision in revisions)
        return [text for text in texts if text is not None]

    def ever_files(self, tag: str, *paths: str) -> list[str]:
        """Returns every path any commit reachable from the tag held under the given paths."""
        logged = self._run("log", "--format=", "--name-only", tag, "--", *paths)
        return sorted({line for line in (logged or "").splitlines() if line})

    def extract(self, tag: str, folder: str, destination: Path) -> None:
        """Unpacks a folder of the tag into a directory, as the tag holds it."""
        done = subprocess.run(
            ["git", "-C", str(self._checkout), "archive", "--format=tar", tag, folder],
            capture_output=True,
        )
        if done.returncode != 0:
            raise SharedToolsError(f"git archive {tag} {folder} failed in {self._checkout}")
        with tarfile.open(fileobj=io.BytesIO(done.stdout)) as archive:
            archive.extractall(destination, filter="data")

    def _run(self, *arguments: str) -> str | None:
        """Returns the text a git command printed, or None when git could not run it or it failed."""
        try:
            done = subprocess.run(
                ["git", "-C", str(self._checkout), "-c", "core.quotepath=off", *arguments],
                capture_output=True,
            )
        except OSError:
            return None
        return done.stdout.decode("utf-8") if done.returncode == 0 else None


def tracked_files(root: Path, *paths: str) -> list[str]:
    """Returns the files git tracks in a repository under the given paths, or none when it is not one."""
    try:
        done = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--", *paths], capture_output=True,
        )
    except OSError:
        return []
    if done.returncode != 0:
        return []
    return [line for line in done.stdout.decode("utf-8").splitlines() if line]
