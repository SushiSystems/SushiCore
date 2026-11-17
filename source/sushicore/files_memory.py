# files_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Text files held in a dictionary, keeping the promise of the `Files` port with no disk."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, final


@final
class MemoryFiles:
    """Files held by path; a folder exists while a file sits under it."""

    def __init__(self, files: Mapping[Path, str] | None = None,
                 modified_times: Mapping[Path, float] | None = None) -> None:
        """Keeps the files given, by path, and the modification times given, by path."""
        self.files: dict[Path, str] = dict(files or {})
        self.modified_times: dict[Path, float] = dict(modified_times or {})

    def is_file(self, path: Path) -> bool:
        """Returns whether a file is at the path."""
        return path in self.files

    def is_dir(self, path: Path) -> bool:
        """Returns whether a file sits anywhere under the path."""
        return any(path in held.parents for held in self.files)

    def exists(self, path: Path) -> bool:
        """Returns whether a file or a folder is at the path."""
        return self.is_file(path) or self.is_dir(path)

    def children(self, folder: Path) -> list[Path]:
        """Returns the files and folders directly in a folder, sorted."""
        found: set[Path] = set()
        for held in self.files:
            if folder in held.parents:
                found.add(folder / held.relative_to(folder).parts[0])
        return sorted(found)

    def read_text(self, path: Path) -> str:
        """Returns a file's text.

        @throws FileNotFoundError When no file is at the path.
        """
        if path not in self.files:
            raise FileNotFoundError(str(path))
        return self.files[path].removeprefix("\ufeff")

    def write_text(self, path: Path, text: str) -> None:
        """Keeps the text at the path, CRLF turned to LF as the disk adapter writes it."""
        self.files[path] = text.replace("\r\n", "\n")

    def remove(self, path: Path) -> None:
        """Drops the file at the path; an absent file is left as it is."""
        self.files.pop(path, None)

    def modified_time(self, path: Path) -> float | None:
        """Returns the time set for the path, or None when none was set."""
        return self.modified_times.get(path)

    def set_modified_time(self, path: Path, seconds: float) -> None:
        """Sets the modification time the path reports."""
        self.modified_times[path] = seconds
