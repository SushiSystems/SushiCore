# lock_file.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The lock file `tools/shared_tools.lock`: the tag, its commit and the hash of each file written."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import final

from ..errors import ConfigError
from ..layered_toml import read_toml
from .errors import NoLockError, SharedToolsError

K_LOCK_PATH = "tools/shared_tools.lock"


def digest(content: bytes) -> str:
    """Returns the SHA-256 of some bytes as hex."""
    return hashlib.sha256(content).hexdigest()


@final
@dataclass(frozen=True, slots=True)
class SharedToolsLock:
    """Holds the SushiCore release the shared files came from and the hash of each as written."""

    tag: str
    commit: str
    files: dict[str, str]

    def render(self) -> str:
        """Returns the TOML text of the lock, files in path order."""
        rows = [f'"{path}" = "{self.files[path]}"' for path in sorted(self.files)]
        return "\n".join([f'tag = "{self.tag}"', f'commit = "{self.commit}"', "", "[files]", *rows, ""])

    def write(self, root: Path) -> None:
        """Writes the lock into a repository."""
        target = root / K_LOCK_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.render(), encoding="utf-8", newline="\n")

    def differing(self, root: Path) -> list[str]:
        """Returns, in path order, each locked file that is missing or whose bytes differ from the lock."""
        names = []
        for path in sorted(self.files):
            target = root / path
            if not target.is_file() or digest(target.read_bytes()) != self.files[path]:
                names.append(path)
        return names


def read_lock(root: Path) -> SharedToolsLock:
    """Returns the lock of a repository; raises NoLockError when it has none."""
    path = root / K_LOCK_PATH
    if not path.is_file():
        raise NoLockError(f"{root} holds no {K_LOCK_PATH}")
    try:
        data = read_toml(path)
        return SharedToolsLock(str(data["tag"]), str(data["commit"]), dict(data.get("files", {})))
    except (ConfigError, KeyError) as error:
        raise SharedToolsError(f"{path} is not a shared tools lock: {error}") from error
