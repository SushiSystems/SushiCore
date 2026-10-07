# bundle_archive.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Packs a staged bundle into a reproducible gzip tar and records its SHA-256."""

from __future__ import annotations

import gzip
import hashlib
import tarfile
from pathlib import Path

K_MODE = 0o644
K_DIGEST_SUFFIX = ".sha256"


def _members(staging: Path) -> list[tuple[str, Path]]:
    """Returns every file under *staging* with its POSIX name, sorted by that name."""
    files = (path for path in staging.rglob("*") if path.is_file())
    return sorted((path.relative_to(staging).as_posix(), path) for path in files)


def write_archive(staging: Path, archive: Path) -> str:
    """Writes the files under *staging* to *archive* and returns the archive's SHA-256.

    Names are sorted and every time, owner and mode is fixed, so the same files give the
    same bytes. The digest is also written to `<archive name>.sha256`.
    """
    archive.parent.mkdir(parents=True, exist_ok=True)
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as packed:
            with tarfile.open(fileobj=packed, mode="w", format=tarfile.GNU_FORMAT) as tar:
                for name, path in _members(staging):
                    member = tarfile.TarInfo(name)
                    member.size = path.stat().st_size
                    member.mode = K_MODE
                    with path.open("rb") as content:
                        tar.addfile(member, content)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    record = archive.with_name(archive.name + K_DIGEST_SUFFIX)
    record.write_bytes(f"{digest}  {archive.name}\n".encode("ascii"))
    return digest
