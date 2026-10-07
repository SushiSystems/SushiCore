# test_bundle_archive.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests that the archive holds the staged files and is the same bytes every time."""

from __future__ import annotations

import hashlib
import os
import tarfile
from pathlib import Path

from sushicore.docs_bundle.bundle_archive import write_archive

from .sample_repository import write_file


def _staging(root: Path) -> Path:
    """Writes a staging folder with a manifest and two pages."""
    write_file(root, "bundle.json", "{}\n")
    write_file(root, "pages/guides/B.md", "# B\n")
    write_file(root, "pages/guides/A.md", "# A\n")
    return root


def test_write_packs_every_file_under_its_posix_name(tmp_path):
    """Stores each staged file, sorted, with no folder entries and fixed metadata."""
    archive = tmp_path / "out" / "docs-bundle-1.2.3.tar.gz"
    write_archive(_staging(tmp_path / "staging"), archive)
    with tarfile.open(archive, "r:gz") as packed:
        members = packed.getmembers()
        assert [member.name for member in members] == [
            "bundle.json",
            "pages/guides/A.md",
            "pages/guides/B.md",
        ]
        assert {(member.mtime, member.uid, member.gid, member.mode) for member in members} == {
            (0, 0, 0, 0o644),
        }
        assert packed.extractfile("pages/guides/A.md").read() == b"# A\n"


def test_write_returns_the_digest_and_writes_it_beside_the_archive(tmp_path):
    """Returns the SHA-256 of the archive and records it in the `.sha256` file."""
    archive = tmp_path / "docs-bundle-1.2.3.tar.gz"
    digest = write_archive(_staging(tmp_path / "staging"), archive)
    assert digest == hashlib.sha256(archive.read_bytes()).hexdigest()
    recorded = (tmp_path / "docs-bundle-1.2.3.tar.gz.sha256").read_bytes()
    assert recorded == f"{digest}  docs-bundle-1.2.3.tar.gz\n".encode("ascii")


def test_write_is_reproducible(tmp_path):
    """Produces the same bytes from the same files written at another time."""
    first = _staging(tmp_path / "first")
    second = _staging(tmp_path / "second")
    for path in second.rglob("*.md"):
        os.utime(path, (1_000_000_000, 1_000_000_000))
    one = write_archive(first, tmp_path / "one.tar.gz")
    two = write_archive(second, tmp_path / "two.tar.gz")
    assert one == two
