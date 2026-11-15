# conftest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Fixtures of the shared tools tests: a tagged SushiCore checkout and a repository to sync."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

K_TAG = "v1.0.0"
K_SHARED = "tools/check_all.py"
K_REAL_TOOLS = Path(__file__).resolve().parents[2] / "tools"


def git(folder: Path, *arguments: str) -> None:
    """Runs git in a folder, with a fixed author and no signing."""
    subprocess.run(
        ["git", "-C", str(folder), "-c", "user.name=t", "-c", "user.email=t@example.com",
         "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *arguments],
        check=True, capture_output=True,
    )


@pytest.fixture(scope="session")
def upstream(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Returns a git repository holding the tools of this repository, committed and tagged."""
    folder = tmp_path_factory.mktemp("upstream") / "sushicore"
    shutil.copytree(K_REAL_TOOLS, folder / "tools", ignore=shutil.ignore_patterns("__pycache__", "tests"))
    (folder / ".github").mkdir()
    (folder / ".github" / "SECURITY.md").write_text("security\n", encoding="utf-8")
    git(folder.parent, "init", "-q", str(folder))
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "-m", "tools")
    git(folder, "tag", K_TAG)
    return folder


@pytest.fixture()
def target(tmp_path: Path) -> Path:
    """Returns a repository folder with a settings file and a README of its own."""
    folder = tmp_path / "target"
    (folder / "tools").mkdir(parents=True)
    (folder / "tools" / "settings.py").write_text("K_OWN = 1\n", encoding="utf-8")
    (folder / "tools" / "README.md").write_text("own readme\n", encoding="utf-8")
    return folder
