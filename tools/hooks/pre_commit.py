# pre_commit.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Runs every checker on the files the commit will hold, not on the files on disk.

Usage: python tools/hooks/pre_commit.py [repository root]

Git runs it through the pre-commit hook; the index is written to a throwaway folder and
`tools/check_all.py` runs there, with git pointed at the real repository.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

K_CHECK_ALL = Path("tools") / "check_all.py"
K_EXIT_REFUSED = 1
K_PREFIX = "pre-commit-"
K_SKIP_HISTORY = "--skip-history"


def absolute_git_dir(root: Path, environ: Mapping[str, str]) -> Path | None:
    """Returns the git directory of the repository at *root*, or None when git cannot name it."""
    done = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--absolute-git-dir"],
        capture_output=True, text=True, env=dict(environ), check=False)
    return Path(done.stdout.strip()) if done.returncode == 0 and done.stdout.strip() else None


def index_file(git_dir: Path, environ: Mapping[str, str]) -> Path:
    """Returns the index git hands the hook: `commit -a` and `-o` give their own."""
    given = environ.get("GIT_INDEX_FILE")
    if not given:
        return git_dir / "index"
    path = Path(given)
    return path if path.is_absolute() else Path(environ.get("GIT_PREFIX", ".")).resolve() / path


def checked_environment(git_dir: Path, tree: Path, environ: Mapping[str, str]) -> dict[str, str]:
    """Returns the environment `check_all.py` runs in: git points at the real repository."""
    return {
        **environ,
        "GIT_DIR": str(git_dir),
        "GIT_WORK_TREE": str(tree),
        "GIT_INDEX_FILE": str(index_file(git_dir, environ)),
        "GIT_OPTIONAL_LOCKS": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def checkout_index(root: Path, tree: Path, environ: Mapping[str, str]) -> str | None:
    """Writes every file of the index below *tree*; returns git's error, or None on success."""
    prefix = tree.as_posix().rstrip("/") + "/"
    done = subprocess.run(
        ["git", "-C", str(root), "checkout-index", "--all", "--force", f"--prefix={prefix}"],
        capture_output=True, text=True, env=dict(environ), check=False)
    return None if done.returncode == 0 else done.stderr.strip() or "git failed"


def check_index(root: Path, git_dir: Path, tree: Path, environ: Mapping[str, str]) -> int:
    """Writes the index to *tree* and returns the exit code of `check_all.py` run there."""
    error = checkout_index(root, tree, environ)
    if error is not None:
        print(f"pre-commit: cannot write the index to {tree}: {error}", file=sys.stderr)
        return K_EXIT_REFUSED
    entry = tree / K_CHECK_ALL
    if not entry.is_file():
        print(f"pre-commit: the index holds no {K_CHECK_ALL.as_posix()}", file=sys.stderr)
        return K_EXIT_REFUSED
    env = checked_environment(git_dir, tree, environ)
    return subprocess.run([sys.executable, str(entry), str(tree), K_SKIP_HISTORY], env=env,
                          check=False).returncode


def remove_folder(folder: Path) -> None:
    """Removes *folder*; a folder that stays is named on stderr, and the commit goes on."""
    try:
        shutil.rmtree(folder)
    except OSError as error:
        print(f"pre-commit: cannot remove {folder}: {error}", file=sys.stderr)


def run(root: Path, environ: Mapping[str, str] | None = None) -> int:
    """Returns the exit code of `check_all.py` run on the index of the repository at *root*.

    The checkers that read every commit are left out: a commit is not in the history yet, and the
    `commit-msg` hook judges its message and its pages.
    """
    environ = dict(os.environ if environ is None else environ)
    git_dir = absolute_git_dir(root, environ)
    if git_dir is None:
        print(f"pre-commit: {root} is not a git repository", file=sys.stderr)
        return K_EXIT_REFUSED
    folder = Path(tempfile.mkdtemp(prefix=K_PREFIX))
    try:
        return check_index(root, git_dir, folder, environ)
    finally:
        remove_folder(folder)


def main(argv: list[str] | None = None) -> int:
    """Runs the checks on the repository named by the argument, or on the current folder."""
    arguments = sys.argv[1:] if argv is None else argv
    return run(Path(arguments[0]) if arguments else Path.cwd())


if __name__ == "__main__":
    sys.exit(main())
