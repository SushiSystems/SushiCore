# test_integrity.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests that a file is accepted only when its SHA-256 is the expected one."""

from __future__ import annotations

import hashlib

import pytest

from sushicore.errors import DigestMismatchError, SushiCoreError
from sushicore.provision.integrity import sha256_of, verify_sha256

K_CONTENT = b"an archive"
K_DIGEST = hashlib.sha256(K_CONTENT).hexdigest()
K_OTHER_DIGEST = hashlib.sha256(b"another archive").hexdigest()


def _file(tmp_path, content: bytes = K_CONTENT):
    """Write *content* to a file under *tmp_path* and return its path."""
    path = tmp_path / "tool.zip"
    path.write_bytes(content)
    return path


def test_sha256_of_returns_the_lower_case_hex_digest(tmp_path):
    """Check that the digest of a file is the lower-case hex SHA-256 of its bytes."""
    assert sha256_of(_file(tmp_path)) == K_DIGEST


def test_verify_accepts_a_file_with_the_expected_digest(tmp_path):
    """Check that a matching file raises nothing."""
    verify_sha256(_file(tmp_path), K_DIGEST)


def test_verify_accepts_an_upper_case_expected_digest(tmp_path):
    """Check that the case a digest was written in does not decide the comparison."""
    verify_sha256(_file(tmp_path), K_DIGEST.upper())


def test_verify_raises_and_names_the_file_and_both_digests(tmp_path):
    """Check that a mismatch raises an error carrying the file, the expected and the actual."""
    path = _file(tmp_path)

    with pytest.raises(DigestMismatchError) as raised:
        verify_sha256(path, K_OTHER_DIGEST)

    assert raised.value.path == path
    assert raised.value.expected == K_OTHER_DIGEST
    assert raised.value.actual == K_DIGEST
    message = str(raised.value)
    assert str(path) in message and K_OTHER_DIGEST in message and K_DIGEST in message


def test_the_mismatch_reaches_the_entry_point_as_a_sushicore_error(tmp_path):
    """Check that the mismatch derives from the error the entry point prints as one line."""
    with pytest.raises(SushiCoreError):
        verify_sha256(_file(tmp_path), K_OTHER_DIGEST)


def test_verify_leaves_the_file_in_place(tmp_path):
    """Check that verifying changes nothing on disk, whichever way it ends."""
    path = _file(tmp_path)

    with pytest.raises(DigestMismatchError):
        verify_sha256(path, K_OTHER_DIGEST)

    assert path.read_bytes() == K_CONTENT
