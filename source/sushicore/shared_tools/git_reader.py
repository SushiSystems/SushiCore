# git_reader.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads files, history and commits of a SushiCore checkout through git, never from its working tree."""

from __future__ import annotations

import io
import tarfile
from pathlib import Path
from typing import final

from ..proc import CommandRunner
from ..quiet_runner import quiet_runner
from .errors import SharedToolsError, TagNotFoundError


@final
class GitReader:
    """Reads one git checkout; every read names the revision it wants."""

    def __init__(self, checkout: Path, runner: CommandRunner | None = None) -> None:
        """Stores the checkout to read and the runner that asks git; the real one when None."""
        self._checkout = checkout
        self._runner = runner if runner is not None else quiet_runner()

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

    def snapshot(self, tag: str, *prefixes: str) -> dict[str, str]:
        """Returns each file of the tag whose path starts with a prefix, read with one git call.

        A text is what `show` returns for the same path; a tag that cannot be archived raises
        SharedToolsError.
        """
        code, packed, _ = self._runner.capture_bytes(
            ["git", "-C", str(self._checkout), "archive", "--format=tar", tag])
        if code != 0:
            raise SharedToolsError(f"git archive {tag} failed in {self._checkout}")
        texts: dict[str, str] = {}
        with tarfile.open(fileobj=io.BytesIO(packed)) as archive:
            for member in archive:
                content = archive.extractfile(member) if member.isfile() else None
                if content is not None and member.name.startswith(prefixes):
                    texts[member.name] = content.read().decode("utf-8").replace("\r\n", "\n")
        return texts

    def history(self, tag: str, path: str) -> list[str]:
        """Returns every text the file held in a commit reachable from the tag, newest first."""
        revisions = (self._run("log", "--format=%H", tag, "--", path) or "").split()
        texts = (self.show(revision, path) for revision in revisions)
        return [text for text in texts if text is not None]

    def revisions(self, path: str) -> list[str]:
        """Returns every commit of any branch or tag that changed the path, newest first."""
        return (self._run("log", "--all", "--format=%H", "--", path) or "").split()

    def ever_files(self, tag: str, *paths: str) -> list[str]:
        """Returns every path any commit reachable from the tag held under the given paths."""
        logged = self._run("log", "--format=", "--name-only", tag, "--", *paths)
        return sorted({line for line in (logged or "").splitlines() if line})

    def extract(self, tag: str, folder: str, destination: Path) -> None:
        """Unpacks a folder of the tag into a directory, as the tag holds it.

        Where `tarfile` has extraction filters the `data` filter is applied; a Python that has none
        extracts the members of the tag's own archive as they are.
        """
        code, packed, _ = self._runner.capture_bytes(
            ["git", "-C", str(self._checkout), "archive", "--format=tar", tag, folder])
        if code != 0:
            raise SharedToolsError(f"git archive {tag} {folder} failed in {self._checkout}")
        with tarfile.open(fileobj=io.BytesIO(packed)) as archive:
            if hasattr(tarfile, "data_filter"):
                archive.extractall(destination, filter="data")
            else:
                archive.extractall(destination)

    def _run(self, *arguments: str) -> str | None:
        """Returns the text a git command printed, or None when git could not run it or it failed."""
        try:
            code, stdout, _ = self._runner.capture_bytes(
                ["git", "-C", str(self._checkout), "-c", "core.quotepath=off", *arguments])
        except OSError:
            return None
        return stdout.decode("utf-8") if code == 0 else None


def tracked_files(root: Path, *paths: str, runner: CommandRunner | None = None) -> list[str]:
    """Returns the files git tracks in a repository under the given paths, or none when it is not one.

    *runner* spawns git; the real one when None.
    """
    try:
        code, stdout, _ = (runner if runner is not None else quiet_runner()).capture_bytes(
            ["git", "-C", str(root), "ls-files", "--", *paths])
    except OSError:
        return []
    if code != 0:
        return []
    return [line for line in stdout.decode("utf-8").splitlines() if line]
