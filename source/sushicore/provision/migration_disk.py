# migration_disk.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What a migration reads from and does to the disk: paths, sizes, copies and removals."""

from __future__ import annotations

import os
import shutil
import stat
import sys
from pathlib import Path
from typing import Callable

from .links import is_dir_link, link_target, make_dir_link, remove_dir_link


#: Appended to the old root's name for the copy kept until ``finalize``.
ASIDE_SUFFIX = ".pre-migrate"

#: Appended to a component's name while its copy is not yet verified.
PARTIAL_SUFFIX = ".partial"


def copy_component(source: Path, target: Path) -> None:
    """Copy the tree at *source* to *target*, recreating links instead of following them."""
    if is_dir_link(source):
        make_dir_link(target, link_target(source))
        return
    junctions: list[Path] = []

    def skip_junctions(folder: str, names: list[str]) -> list[str]:
        """Return the names copytree must leave out, which are the junctions."""
        found = [n for n in names if _is_junction_only(Path(folder) / n)]
        junctions.extend(Path(folder) / n for n in found)
        return found

    shutil.copytree(source, target, symlinks=True, ignore=skip_junctions)
    for junction in junctions:
        make_dir_link(target / junction.relative_to(source), link_target(junction))


def verify_component(source: Path, copy: Path) -> bool:
    """Report whether *copy* holds the same files as *source*, each of the same size."""
    return file_sizes(source) == file_sizes(copy)


def file_sizes(root: Path) -> dict[str, int]:
    """Return the size of every file under *root* by relative path, a link counting as 0."""
    if is_dir_link(root):
        return {"": 0}
    sizes: dict[str, int] = {}
    prefix = len(str(root)) + 1
    pending = [str(root)]
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                key = entry.path[prefix:].replace(os.sep, "/")
                if entry.is_symlink():
                    sizes[key] = 0
                elif entry.is_dir(follow_symlinks=False):
                    if is_dir_link(Path(entry.path)):
                        sizes[key] = 0
                    else:
                        pending.append(entry.path)
                else:
                    sizes[key] = entry.stat(follow_symlinks=False).st_size
    return sizes


def remove_tree(path: Path) -> None:
    """Delete *path* whatever it is: a link alone, or a tree with its read-only files."""
    if is_dir_link(path):
        remove_dir_link(path)
    elif path.is_dir():
        if sys.version_info >= (3, 12):
            shutil.rmtree(path, onexc=_clear_read_only)
        else:
            shutil.rmtree(path, onerror=_clear_read_only)
    elif path.exists():
        path.unlink()


def _clear_read_only(function: Callable[[str], None], path: str, _error: object) -> None:
    """Make *path* writable and repeat the removal that failed on it."""
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    function(path)


def _is_junction_only(path: Path) -> bool:
    """Report whether *path* is a directory link that is not a symlink."""
    return is_dir_link(path) and not path.is_symlink()



def is_present(path: Path) -> bool:
    """Report whether *path* exists, a link with a missing target included."""
    return path.exists() or is_dir_link(path)


def absolute(path: Path) -> Path:
    """Return *path* as an absolute path without resolving a link."""
    return Path(os.path.abspath(path))


def aside_path(old_root: Path) -> Path:
    """Return where the old root is kept until ``finalize``."""
    return old_root.with_name(old_root.name + ASIDE_SUFFIX)


def partial_path(target: Path) -> Path:
    """Return where a component is copied before it is verified."""
    return target.with_name(target.name + PARTIAL_SUFFIX)


def existing_ancestor(path: Path) -> Path:
    """Return *path*, or the nearest directory above it that exists."""
    current = absolute(path)
    while not current.exists() and current != current.parent:
        current = current.parent
    return current


def same_volume(old_root: Path, new_root: Path) -> bool:
    """Report whether the two roots are on one volume, so a rename can move between them."""
    old_device = os.stat(existing_ancestor(old_root)).st_dev
    return old_device == os.stat(existing_ancestor(new_root)).st_dev
