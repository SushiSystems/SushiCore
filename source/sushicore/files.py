# files.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The file-system port a store reads and writes its text files through, and its disk adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class Files(Protocol):
    """The text files and folders a store needs, addressed by path."""

    def is_file(self, path: Path) -> bool:
        """Returns whether a file is at the path."""

    def is_dir(self, path: Path) -> bool:
        """Returns whether a folder is at the path."""

    def exists(self, path: Path) -> bool:
        """Returns whether a file or a folder is at the path."""

    def children(self, folder: Path) -> list[Path]:
        """Returns the files and folders directly in a folder, sorted; an absent folder has none."""

    def read_text(self, path: Path) -> str:
        """Returns a file's text read as UTF-8, a byte order mark dropped.

        @throws FileNotFoundError When no file is at the path.
        """

    def write_text(self, path: Path, text: str) -> None:
        """Writes a file as UTF-8 with LF line ends, its folders made first."""

    def remove(self, path: Path) -> None:
        """Removes the file at the path; an absent file is left as it is."""


class DiskFiles:
    """The files of the real file system."""

    def is_file(self, path: Path) -> bool:
        """Returns whether a file is at the path."""
        return path.is_file()

    def is_dir(self, path: Path) -> bool:
        """Returns whether a folder is at the path."""
        return path.is_dir()

    def exists(self, path: Path) -> bool:
        """Returns whether a file or a folder is at the path."""
        return path.exists()

    def children(self, folder: Path) -> list[Path]:
        """Returns the files and folders directly in a folder, sorted; an absent folder has none."""
        return sorted(folder.iterdir()) if folder.is_dir() else []

    def read_text(self, path: Path) -> str:
        """Returns a file's text read as UTF-8, a byte order mark dropped."""
        return path.read_text(encoding="utf-8-sig")

    def write_text(self, path: Path, text: str) -> None:
        """Writes a file as UTF-8 with LF line ends, its folders made first."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def remove(self, path: Path) -> None:
        """Removes the file at the path; an absent file is left as it is."""
        path.unlink(missing_ok=True)
