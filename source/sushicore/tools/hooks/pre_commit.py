# pre_commit.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Runs every checker on the files the commit will hold.

Usage: python -m sushicore.tools.hooks.pre_commit [repository root]

Git runs it through the pre-commit hook: in place when the disk holds the index, otherwise on the
index written beside the repository, with the working tree left as it is.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from sushicore.tools.hooks.index_tree import IndexTree, differing_files
from sushicore.tools.repo_settings import K_ROOT_VARIABLE, K_SETTINGS

#: The module that runs every check.
K_CHECK_ALL = "sushicore.tools.check_all"
K_EXIT_REFUSED = 1
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


def checked_environment(git_dir: Path, root: Path, environ: Mapping[str, str]) -> dict[str, str]:
    """Returns the environment `check_all.py` runs in: git reads the index the commit holds."""
    return {
        **environ,
        "GIT_DIR": str(git_dir),
        "GIT_WORK_TREE": str(root),
        "GIT_INDEX_FILE": str(index_file(git_dir, environ)),
        "GIT_OPTIONAL_LOCKS": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        K_ROOT_VARIABLE: str(root),
    }


def staged(root: Path, path: Path, environ: Mapping[str, str]) -> bool:
    """Returns whether the index holds *path*."""
    done = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", path.as_posix()],
        capture_output=True, text=True, env=dict(environ), check=False)
    return done.returncode == 0


def refusal(root: Path, environ: Mapping[str, str]) -> str | None:
    """Returns why the index of the repository at *root* cannot be checked, or None when it can."""
    if not staged(root, K_SETTINGS, environ):
        return f"the index holds no {K_SETTINGS.as_posix()}"
    return None


def check_tree(tree: Path, git_dir: Path, environ: Mapping[str, str],
               check: Sequence[str] | None) -> int:
    """Returns the exit code of the checks run on *tree*, with git reading the repository's index."""
    command = list(check) if check is not None else [sys.executable, "-m", K_CHECK_ALL]
    return subprocess.run([*command, str(tree), K_SKIP_HISTORY], cwd=tree,
                          env=checked_environment(git_dir, tree, environ), check=False).returncode


def run(root: Path, environ: Mapping[str, str] | None = None, check: Sequence[str] | None = None) -> int:
    """Returns the exit code of the checks run on the index of the repository at *root*.

    The checkers that read every commit are left out: a commit is not in the history yet, and the
    `commit-msg` hook judges its message and its pages. *check* is the command that runs the checks,
    the root and the option following it; `python -m sushicore.tools.check_all` when None.
    """
    environ = dict(os.environ if environ is None else environ)
    git_dir = absolute_git_dir(root, environ)
    if git_dir is None:
        print(f"pre-commit: {root} is not a git repository", file=sys.stderr)
        return K_EXIT_REFUSED
    differing = differing_files(root, environ)
    problem = "git cannot read the index" if differing is None else refusal(root, environ)
    if problem is not None:
        print(f"pre-commit: {problem}", file=sys.stderr)
        return K_EXIT_REFUSED
    if not differing:
        return check_tree(root.resolve(), git_dir, environ, check)
    with IndexTree(root, environ) as tree:
        problem = tree.write(differing)
        if problem is None and tree.path is not None:
            code = check_tree(tree.path, git_dir, environ, check)
        else:
            print(f"pre-commit: {problem}", file=sys.stderr)
            code = K_EXIT_REFUSED
    for line in tree.problems:
        print(f"pre-commit: {line}", file=sys.stderr)
    return code


def main(argv: list[str] | None = None) -> int:
    """Runs the checks on the repository named by the argument, or on the current folder."""
    arguments = sys.argv[1:] if argv is None else argv
    return run(Path(arguments[0]) if arguments else Path.cwd())


if __name__ == "__main__":
    sys.exit(main())
