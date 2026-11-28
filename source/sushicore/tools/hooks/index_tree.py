# index_tree.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Writes the tree the index holds into a folder beside the repository, and removes it again.

A file whose disk copy equals the index is hard linked, so the tree costs no copy and the working
tree's files keep their bytes and times; a file that differs is written from the index.
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
#: The file in a tree folder that names the repository the tree belongs to.
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


def ignored_files(root: Path, environ: Mapping[str, str]) -> list[str] | None:
    """Returns the ignored files outside an ignored folder, or None when git fails."""
    done = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--others", "--ignored", "--exclude-standard",
         "--directory", "-z"],
        capture_output=True, text=True, env=dict(environ), check=False)
    if done.returncode != 0:
        return None
    return [entry for entry in done.stdout.split("\0") if entry and not entry.endswith("/")]


def tree_prefix(root: Path) -> str:
    """Returns the name every tree folder of the repository at *root* starts with."""
    return f".{root.resolve().name}{K_TREE_MARK}"


def is_tree_of(folder: Path, root: Path) -> bool:
    """Returns whether *folder* is a tree folder that names the repository at *root* as its own."""
    try:
        owner = (folder / K_OWNER_FILE).read_text(encoding="utf-8").strip()
    except OSError:
        return False
    return owner == str(root.resolve())


def remove_stale_trees(root: Path, submodules: Sequence[str]) -> None:
    """Removes the tree folders of the repository at *root* that an earlier commit left.

    Git holds the index lock while the hook runs, so no other commit of the repository is live.
    """
    for folder in root.resolve().parent.glob(f"{tree_prefix(root)}*"):
        if folder.is_dir() and is_tree_of(folder, root):
            remove_tree(folder, submodules)


def link_file(source: Path, target: Path) -> None:
    """Makes *target* a hard link to *source*, or a copy where the disk refuses the link."""
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


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


def remove_tree(tree: Path, submodules: Sequence[str]) -> str | None:
    """Removes *tree*, unlinking its submodule links first; returns the error, or None."""
    for path in submodules:
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
        self.submodules: list[str] = []
        self.problems: list[str] = []

    def __enter__(self) -> IndexTree:
        return self

    def __exit__(self, *_: object) -> None:
        if self.path is not None:
            error = remove_tree(self.path, self.submodules)
            if error is not None:
                self.problems.append(f"cannot remove {self.path}: {error}")

    def write(self, differing: Sequence[str]) -> str | None:
        """Writes the tree, *differing* from the index and the rest linked; returns why it failed."""
        entries = index_entries(self.root, self.environ)
        if entries is None:
            return "git cannot read the index"
        ignored = ignored_files(self.root, self.environ)
        if ignored is None:
            return "git cannot list the ignored files"
        self.submodules = [name for mode, name in entries if mode == K_GITLINK_MODE]
        remove_stale_trees(self.root, self.submodules)
        self.path = Path(tempfile.mkdtemp(prefix=tree_prefix(self.root), dir=self.root.parent))
        (self.path / K_OWNER_FILE).write_text(f"{self.root}\n", encoding="utf-8")
        changed = set(differing)
        from_index: list[str] = []
        for mode, name in entries:
            if mode == K_GITLINK_MODE:
                continue
            if mode == K_SYMLINK_MODE or name in changed or not (self.root / name).is_file():
                from_index.append(name)
            else:
                link_file(self.root / name, self.path / name)
        error = checkout_paths(self.root, self.path, from_index, self.environ)
        if error is not None:
            return f"cannot write the index to {self.path}: {error}"
        for name in ignored:
            if (self.root / name).is_file() and not (self.path / name).exists():
                link_file(self.root / name, self.path / name)
        for name in self.submodules:
            problem = link_folder(self.root / name, self.path / name)
            if problem is not None:
                self.problems.append(f"cannot link the submodule {name}: {problem}")
        return None
