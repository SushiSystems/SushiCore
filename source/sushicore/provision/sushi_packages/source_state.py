# source_state.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Hashes the source content of a library checkout, leaving out what does not change a build."""

from __future__ import annotations

import fnmatch
import hashlib
import subprocess
from pathlib import Path, PurePosixPath
from typing import Protocol, Sequence

from .package_error import PackageError

#: The top-level folders whose content never enters the hash.
K_EXCLUDED_FOLDERS = ("docs", "build")

#: The prefix of the build folders that never enter the hash, such as ``build-asan``.
K_BUILD_PREFIX = "build-"

#: The suffix of the pages that never enter the hash.
K_PAGE_SUFFIX = ".md"


class ISourceInspector(Protocol):
    """What the source hash asks a checkout."""

    def files(self, checkout: Path) -> list[Path]:
        """Return the tracked and the untracked, not ignored files, relative to *checkout*."""


class GitSourceInspector:
    """Asks the git on PATH."""

    def files(self, checkout: Path) -> list[Path]:
        """Run ``git ls-files --cached --others --exclude-standard -z``.

        Raises:
            PackageError: *checkout* is not a git repository, or git cannot run.
        """
        command = ["git", "-C", str(checkout), "ls-files", "--cached", "--others",
                   "--exclude-standard", "-z"]
        try:
            result = subprocess.run(command, capture_output=True)
        except OSError as exc:
            raise PackageError(f"git cannot run in {checkout}: {exc}") from exc
        if result.returncode != 0:
            raise PackageError(f"{checkout} is not a git checkout, so its source is unknown.")
        names = result.stdout.decode("utf-8", "replace").split("\0")
        return sorted({Path(name) for name in names if name})


def is_excluded(relative: Path, excludes: Sequence[str]) -> bool:
    """Report whether *relative* stays out of the hash.

    The built-in exclusions are ``docs/``, ``build/``, ``build-*/`` and every ``*.md``. An entry
    of *excludes* ending in ``/`` is a folder prefix; any other entry is a glob over the path.
    """
    posix = PurePosixPath(relative.as_posix())
    first = posix.parts[0] if posix.parts else ""
    if first in K_EXCLUDED_FOLDERS and len(posix.parts) > 1:
        return True
    if first.startswith(K_BUILD_PREFIX) and len(posix.parts) > 1:
        return True
    if posix.suffix == K_PAGE_SUFFIX:
        return True
    text = posix.as_posix()
    return any(text.startswith(entry) if entry.endswith("/") else fnmatch.fnmatch(text, entry)
               for entry in excludes)


def describe_source(checkout: Path, inspector: ISourceInspector,
                    excludes: Sequence[str] = ()) -> str:
    """Return the SHA-256, as hex, of the path and bytes of the source files of *checkout*.

    A file the working tree no longer holds is skipped, so a deletion that git has not staged
    changes the hash as it changes the build.

    Args:
        checkout: The library's checkout.
        inspector: Lists the files.
        excludes: The ``package_exclude`` entries of the library's fragment.

    Raises:
        PackageError: *checkout* is not a git repository, or a file cannot be read.
    """
    digest = hashlib.sha256()
    for relative in inspector.files(checkout):
        if is_excluded(relative, excludes):
            continue
        path = checkout / relative
        if not path.is_file():
            continue
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise PackageError(f"cannot read {path}: {exc}") from exc
        digest.update(relative.as_posix().encode("utf-8") + b"\0")
        digest.update(len(content).to_bytes(8, "little") + content)
    return digest.hexdigest()
