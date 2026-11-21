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
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

K_CHECK_ALL = Path("tools") / "check_all.py"
K_EXIT_REFUSED = 1
K_PREFIX = "pre-commit-"


def absolute_git_dir(root: Path, environ: Mapping[str, str]) -> Path | None:
    """Returns the git directory of the repository at *root*, or None when git cannot name it."""
    done = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--absolute-git-dir"],
        capture_output=True, text=True, env=dict(environ), check=False)
    return Path(done.stdout.strip()) if done.returncode == 0 and done.stdout.strip() else None


def index_file(git_dir: Path, environ: Mapping[str, str]) -> Path:
    """Returns the index git hands the hook: its own for `commit -a` and `-o`, else the repository's."""
    given = environ.get("GIT_INDEX_FILE")
    if not given:
        return git_dir / "index"
    path = Path(given)
    return path if path.is_absolute() else Path(environ.get("GIT_PREFIX", ".")).resolve() / path


def checkout_index(root: Path, tree: Path, environ: Mapping[str, str]) -> bool:
    """Writes every file of the index below *tree*; returns whether git succeeded."""
    prefix = tree.as_posix().rstrip("/") + "/"
    done = subprocess.run(
        ["git", "-C", str(root), "checkout-index", "--all", "--force", f"--prefix={prefix}"],
        capture_output=True, text=True, env=dict(environ), check=False)
    if done.returncode != 0:
        print(f"pre-commit: cannot write the index to {tree}: {done.stderr.strip()}", file=sys.stderr)
    return done.returncode == 0


def run(root: Path, environ: Mapping[str, str] | None = None) -> int:
    """Returns the exit code of `check_all.py` run on the index of the repository at *root*.

    A red file on disk that the commit does not hold cannot refuse it, and a fix on disk cannot
    let a red staged file through. The index git hands the hook is the one read, so `git commit -a`,
    `-o` and `--amend` check what they will commit.
    """
    environ = dict(os.environ if environ is None else environ)
    git_dir = absolute_git_dir(root, environ)
    if git_dir is None:
        print(f"pre-commit: {root} is not a git repository", file=sys.stderr)
        return K_EXIT_REFUSED
    with tempfile.TemporaryDirectory(prefix=K_PREFIX, ignore_cleanup_errors=True) as folder:
        tree = Path(folder)
        if not checkout_index(root, tree, environ):
            return K_EXIT_REFUSED
        checked = {
            **environ,
            "GIT_DIR": str(git_dir),
            "GIT_WORK_TREE": str(tree),
            "GIT_INDEX_FILE": str(index_file(git_dir, environ)),
            "GIT_OPTIONAL_LOCKS": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        entry = tree / K_CHECK_ALL
        if not entry.is_file():
            print(f"pre-commit: the index holds no {K_CHECK_ALL.as_posix()}", file=sys.stderr)
            return K_EXIT_REFUSED
        return subprocess.run([sys.executable, str(entry), str(tree)], env=checked, check=False).returncode


def main(argv: list[str] | None = None) -> int:
    """Runs the checks on the repository named by the argument, or on the current folder."""
    arguments = sys.argv[1:] if argv is None else argv
    return run(Path(arguments[0]) if arguments else Path.cwd())


if __name__ == "__main__":
    sys.exit(main())
