# links.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Creates, inspects and removes directory links: junctions on Windows, symlinks elsewhere."""

from __future__ import annotations

import os
import stat
from pathlib import Path

_IS_WINDOWS = os.name == "nt"

#: The prefix Windows puts before the target a junction stores.
_EXTENDED_PREFIX = "\\\\?\\"


def make_dir_link(link: Path, target: Path) -> None:
    """Create *link* as a directory link to *target*.

    Raises:
        FileExistsError: *link* already exists.
    """
    if link.exists() or is_dir_link(link):
        raise FileExistsError(str(link))
    if _IS_WINDOWS:
        import _winapi
        _winapi.CreateJunction(str(target.resolve()), str(link))
    else:
        os.symlink(target.resolve(), link, target_is_directory=True)


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
    if _IS_WINDOWS:
        os.rmdir(path)
    else:
        path.unlink()


def _is_junction(path: Path) -> bool:
    """Report whether *path* is a Windows junction, read from its reparse tag."""
    if not _IS_WINDOWS:
        return False
    try:
        tag = os.lstat(path).st_reparse_tag
    except OSError:
        return False
    return tag == stat.IO_REPARSE_TAG_MOUNT_POINT
