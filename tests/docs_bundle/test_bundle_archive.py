# test_bundle_archive.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the archive holds the staged files and is the same bytes every time."""

from __future__ import annotations

import hashlib
import os
import tarfile
from pathlib import Path

import pytest

from sushicore.docs_bundle.bundle_archive import write_archive

from .sample_repository import write_file


pytestmark = pytest.mark.medium

K_NAME = "docs-bundle-1.2.3.tar.gz"


def _staging(root: Path, mtime: int | None = None) -> Path:
    """Writes a staging folder with a manifest and two pages, all stamped *mtime* when given."""
    paths = [
        write_file(root, "bundle.json", "{}\n"),
        write_file(root, "pages/guides/B.md", "# B\n"),
        write_file(root, "pages/guides/A.md", "# A\n"),
    ]
    for path in paths if mtime is not None else []:
        os.utime(path, (mtime, mtime))
    return root


def _contents(archive: Path) -> dict[str, bytes]:
    """Returns the bytes of every file member of *archive*, in the order they are stored."""
    with tarfile.open(archive, "r:gz") as packed:
        return {member.name: packed.extractfile(member).read() for member in packed.getmembers()}


def _metadata(archive: Path) -> set[tuple[int, int, int, int]]:
    """Returns the distinct (mtime, uid, gid, mode) of the members of *archive*."""
    with tarfile.open(archive, "r:gz") as packed:
        return {(m.mtime, m.uid, m.gid, m.mode) for m in packed.getmembers()}


def test_write_stores_each_file_under_its_posix_name_sorted(tmp_path):
    """Stores each staged file with its staged bytes, sorted, with no folder entries."""
    archive = tmp_path / "out" / K_NAME
    write_archive(_staging(tmp_path / "staging"), archive)
    assert _contents(archive) == {
        "bundle.json": b"{}\n",
        "pages/guides/A.md": b"# A\n",
        "pages/guides/B.md": b"# B\n",
    }
    assert list(_contents(archive)) == ["bundle.json", "pages/guides/A.md", "pages/guides/B.md"]


def test_write_fixes_the_time_owner_and_mode_of_every_member(tmp_path):
    """Gives every member mtime 0, owner 0, group 0 and mode 0644."""
    archive = tmp_path / K_NAME
    write_archive(_staging(tmp_path / "staging", mtime=1_000_000_000), archive)
    assert _metadata(archive) == {(0, 0, 0, 0o644)}


def test_write_returns_the_sha256_of_the_archive(tmp_path):
    """Returns the SHA-256 of the archive's bytes."""
    archive = tmp_path / K_NAME
    digest = write_archive(_staging(tmp_path / "staging"), archive)
    assert digest == hashlib.sha256(archive.read_bytes()).hexdigest()


def test_write_records_the_digest_beside_the_archive(tmp_path):
    """Writes the digest line to the `.sha256` file next to the archive."""
    archive = tmp_path / K_NAME
    digest = write_archive(_staging(tmp_path / "staging"), archive)
    recorded = (tmp_path / f"{K_NAME}.sha256").read_bytes()
    assert recorded == f"{digest}  {K_NAME}\n".encode("ascii")


def test_write_gives_the_same_bytes_whatever_the_file_times(tmp_path):
    """Produces the same digest from the same files stamped at another time."""
    first = _staging(tmp_path / "first")
    second = _staging(tmp_path / "second", mtime=1_000_000_000)
    one = write_archive(first, tmp_path / "one.tar.gz")
    two = write_archive(second, tmp_path / "two.tar.gz")
    assert one == two
