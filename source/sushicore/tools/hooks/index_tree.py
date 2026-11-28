# index_tree.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Writes the tree the index holds into a folder beside the repository, and removes it again.

A file that differs from the index is written from it, every other file is copied from the disk,
and submodules and ignored folders are folder links, so the working tree is read and never written.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

#: The mode git gives a submodule entry of the index.
K_GITLINK_MODE = "160000"
#: The mode git gives a symbolic link entry of the index.
K_SYMLINK_MODE = "120000"
#: The name of a tree folder, after a dot and the repository's name.
K_TREE_MARK = "-pre-commit-"
#: The file in a tree folder that names its repository, then each of its folder links, one a line.
K_OWNER_FILE = ".sushicore-pre-commit"


def differing_files(root: Path, environ: Mapping[str, str]) -> list[str] | None:
    """Returns the index entries whose disk copy differs from the index, or None when git fails."""
    done = subprocess.run(
        ["git", "-C", str(root), "diff", "--name-only", "--no-renames", "-z"],
        capture_output=True, text=True, env=dict(environ), check=False)
    if done.returncode != 0:
        return None
    return [name for name in done.stdout.split("\0") if name]


def index_entries(root: Path, environ: Mapping[str, str]) -> list[tuple[str, str]] | None:
    """Returns each index entry as its mode and its path, or None when git cannot read the index."""
    done = subprocess.run(["git", "-C", str(root), "ls-files", "--stage", "-z"],
                          capture_output=True, text=True, env=dict(environ), check=False)
    if done.returncode != 0:
        return None
    entries = [entry.partition("\t") for entry in done.stdout.split("\0") if entry]
    return [(meta.split(" ", 1)[0], path) for meta, _, path in entries]


def ignored_paths(root: Path, environ: Mapping[str, str]) -> list[str] | None:
    """Returns the ignored files and folders, a folder ending in `/`, or None when git fails."""
    done = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--others", "--ignored", "--exclude-standard",
         "--directory", "-z"],
        capture_output=True, text=True, env=dict(environ), check=False)
    if done.returncode != 0:
        return None
    return [entry for entry in done.stdout.split("\0") if entry]


def outermost(paths: Sequence[str]) -> list[str]:
    """Returns the ignored paths that lie in no ignored folder of *paths*, a folder ending in `/`.

    Git lists the files of an ignored folder beside it when the folder holds its own ignore file.
    """
    folders = [path for path in paths if path.endswith("/")]
    return [path for path in paths
            if not any(path != folder and path.startswith(folder) for folder in folders)]


def tree_prefix(root: Path) -> str:
    """Returns the name every tree folder of the repository at *root* starts with."""
    return f".{root.resolve().name}{K_TREE_MARK}"


def owner_lines(folder: Path) -> list[str]:
    """Returns the lines of the owner file of *folder*, or none when it has no readable one."""
    try:
        return (folder / K_OWNER_FILE).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []


def remove_stale_trees(root: Path) -> None:
    """Removes the tree folders of the repository at *root* that an earlier commit left.

    Git holds the index lock while the hook runs, so no other commit of the repository is live.
    """
    for folder in root.resolve().parent.glob(f"{tree_prefix(root)}*"):
        lines = owner_lines(folder) if folder.is_dir() else []
        if lines and lines[0] == str(root.resolve()):
            remove_tree(folder, lines[1:])


def copy_file(source: Path, target: Path) -> None:
    """Copies the content and the mode of *source* to *target*."""
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(source, target)


def link_folder(source: Path, target: Path) -> str | None:
    """Makes *target* a link to the folder *source*; returns the error, or None.

    A submodule that is not checked out has nothing to read and is left out.
    """
    if not source.is_dir():
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(source, target, target_is_directory=True)
        return None
    except OSError as error:
        if os.name != "nt":
            return str(error)
    try:
        import _winapi
        _winapi.CreateJunction(str(source), str(target))
        return None
    except OSError as error:
        return str(error)


def checkout_paths(root: Path, tree: Path, paths: Sequence[str],
                   environ: Mapping[str, str]) -> str | None:
    """Writes *paths* from the index below *tree*; returns git's error, or None."""
    if not paths:
        return None
    prefix = tree.as_posix().rstrip("/") + "/"
    done = subprocess.run(
        ["git", "-C", str(root), "checkout-index", "--force", "-z", "--stdin",
         f"--prefix={prefix}"],
        input="\0".join(paths) + "\0", capture_output=True, text=True, env=dict(environ),
        check=False)
    return None if done.returncode == 0 else done.stderr.strip() or "git failed"


def unlink_folder(target: Path) -> None:
    """Removes the folder link *target* and nothing behind it; a path that is no link stays."""
    try:
        target.unlink()
    except OSError:
        try:
            os.rmdir(target)
        except OSError:
            return


def remove_tree(tree: Path, links: Sequence[str]) -> str | None:
    """Removes *tree*, unlinking its folder links first; returns the error, or None."""
    for path in links:
        unlink_folder(tree / path)
    try:
        shutil.rmtree(tree)
    except OSError as error:
        return str(error)
    return None


class IndexTree:
    """The tree a commit will hold, written beside the repository at *root* and removed on exit."""

    def __init__(self, root: Path, environ: Mapping[str, str]) -> None:
        self.root = root.resolve()
        self.environ = dict(environ)
        self.path: Path | None = None
        self.links: list[str] = []
        self.problems: list[str] = []

    def __enter__(self) -> IndexTree:
        return self

    def __exit__(self, *_: object) -> None:
        if self.path is not None:
            error = remove_tree(self.path, self.links)
            if error is not None:
                self.problems.append(f"cannot remove {self.path}: {error}")

    def write(self, differing: Sequence[str]) -> str | None:
        """Writes the tree, *differing* from the index and the rest from disk; returns why it failed."""
        entries = index_entries(self.root, self.environ)
        if entries is None:
            return "git cannot read the index"
        listed = ignored_paths(self.root, self.environ)
        if listed is None:
            return "git cannot list the ignored files"
        ignored = outermost(listed)
        remove_stale_trees(self.root)
        self.path = Path(tempfile.mkdtemp(prefix=tree_prefix(self.root), dir=self.root.parent))
        folders = [name for mode, name in entries if mode == K_GITLINK_MODE]
        folders += [name.rstrip("/") for name in ignored if name.endswith("/")]
        (self.path / K_OWNER_FILE).write_text(
            "".join(f"{line}\n" for line in [str(self.root), *folders]), encoding="utf-8")
        self.links = folders
        changed = set(differing)
        from_index: list[str] = []
        for mode, name in entries:
            if mode == K_GITLINK_MODE:
                continue
            if mode == K_SYMLINK_MODE or name in changed or not (self.root / name).is_file():
                from_index.append(name)
            else:
                copy_file(self.root / name, self.path / name)
        error = checkout_paths(self.root, self.path, from_index, self.environ)
        if error is not None:
            return f"cannot write the index to {self.path}: {error}"
        for name in ignored:
            if not name.endswith("/") and (self.root / name).is_file():
                copy_file(self.root / name, self.path / name)
        for name in folders:
            problem = link_folder(self.root / name, self.path / name)
            if problem is not None:
                self.problems.append(f"cannot link the folder {name}: {problem}")
        return None
