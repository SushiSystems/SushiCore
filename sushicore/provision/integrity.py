# integrity.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Verifies a file against an expected SHA-256 digest."""

from __future__ import annotations

import hashlib
from pathlib import Path

from sushicore.errors import DigestMismatchError

#: Bytes read per step while hashing a file.
K_CHUNK_BYTES = 1 << 20


def sha256_of(path: Path) -> str:
    """Return the lower-case hex SHA-256 of the file at *path*."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(K_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256(path: Path, expected: str) -> None:
    """Check that the file at *path* has the SHA-256 *expected*.

    Args:
        expected: The hex digest, in either case.

    Raises:
        DigestMismatchError: The file's digest differs; the file is left as it is.
    """
    actual = sha256_of(path)
    if actual != expected.lower():
        raise DigestMismatchError(path, expected.lower(), actual)
