# links.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Creates, inspects and removes directory links: junctions on Windows, symlinks elsewhere."""

from __future__ import annotations

import os
from pathlib import Path

from .host import current_host

#: The prefix Windows puts before the target a junction stores.
_EXTENDED_PREFIX = "\\\\?\\"


def make_dir_link(link: Path, target: Path) -> None:
    """Create *link* as a directory link to *target*.

    Raises:
        FileExistsError: *link* already exists.
    """
    if link.exists() or is_dir_link(link):
        raise FileExistsError(str(link))
    current_host().make_dir_link(link, target)


def is_dir_link(path: Path) -> bool:
    """Report whether *path* is a junction or a directory symlink."""
    return path.is_symlink() or _is_junction(path)


def link_target(path: Path) -> Path | None:
    """Return the directory *path* links to, or None when it is not a link."""
    if not is_dir_link(path):
        return None
    target = os.readlink(path)
    if target.startswith(_EXTENDED_PREFIX):
        target = target[len(_EXTENDED_PREFIX):]
    return Path(target)


def remove_dir_link(path: Path) -> None:
    """Remove the link at *path* without touching the directory it points to.

    Raises:
        ValueError: *path* is not a directory link.
    """
    if not is_dir_link(path):
        raise ValueError(f"{path} is not a directory link")
    current_host().remove_dir_link(path)


def _is_junction(path: Path) -> bool:
    """Report whether *path* is a Windows junction, read from its reparse tag."""
    return current_host().is_junction(path)
