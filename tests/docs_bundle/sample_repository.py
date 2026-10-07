# sample_repository.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Builds the small repository the documentation bundle tests read."""

from __future__ import annotations

import subprocess
from pathlib import Path

K_PUBLISH = """name = "sample"
title = "Sample"
summary = "A sample repository."
sections = ["architecture", "guides"]
source_url = "https://github.com/SushiSystems/Sample/"
"""

K_FILES = {
    "README.md": "# Sample\n",
    "docs/publish.toml": K_PUBLISH,
    "docs/README.md": (
        "# Manual\n\n"
        "- [Overview](architecture/OVERVIEW.md)\n"
        "- [Building](guides/BUILDING.md)\n"
        "- [FAQ](guides/FAQ.md)\n"
        "- [Secret](design/SECRET.md)\n"
    ),
    "docs/architecture/OVERVIEW.md": (
        "# Overview\n\nThe design is in [the secret](../design/SECRET.md).\n"
    ),
    "docs/guides/BUILDING.md": (
        "# Building\n\n"
        "Read [the overview](../architecture/OVERVIEW.md#layers) and [the root](../../README.md).\n\n"
        "![A shot](images/shot.png)\n"
    ),
    "docs/guides/FAQ.md": "# FAQ\n\n## Does it build?\n\nYes.\n",
    "docs/design/SECRET.md": "# Secret\n",
}
K_SHOT = b"\x89PNG\r\n\x1a\n"


def write_file(root: Path, relative: str, text: str) -> Path:
    """Writes one file below *root*, creating its folders, and returns its path."""
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def build_sample(root: Path) -> Path:
    """Writes the sample repository below *root* and returns *root*."""
    for relative, text in K_FILES.items():
        write_file(root, relative, text)
    (root / "docs" / "guides" / "images").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "guides" / "images" / "shot.png").write_bytes(K_SHOT)
    return root


def run_git(root: Path, *arguments: str) -> str:
    """Runs git in *root* with a fixed identity and no signing, and returns its output."""
    command = [
        "git", "-c", "user.name=t", "-c", "user.email=t@t.io", "-c", "commit.gpgsign=false",
        *arguments,
    ]
    done = subprocess.run(command, cwd=root, check=True, capture_output=True, text=True)
    return done.stdout.strip()


def commit_all(root: Path) -> str:
    """Makes *root* a git repository holding one commit of its files and returns the hash."""
    run_git(root, "init", "-q")
    run_git(root, "add", "-A")
    run_git(root, "commit", "-q", "-m", "sample")
    return run_git(root, "rev-parse", "HEAD")
