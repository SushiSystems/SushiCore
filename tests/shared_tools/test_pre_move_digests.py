# test_pre_move_digests.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the pre-move digests: the pure judgement and the reader of the frozen file."""

from __future__ import annotations

import pytest

from sushicore.shared_tools import SharedToolsError
from sushicore.shared_tools.pre_move_digests import (
    K_DIGESTS_PATH,
    body_digest,
    is_pre_move_copy,
    read_pre_move_digests,
)

pytestmark = pytest.mark.small

K_ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_body_digest_is_the_sha256_of_the_utf8_text():
    """The digest of "abc" is the published SHA-256 test vector."""
    assert body_digest("abc") == K_ABC


def test_a_body_with_a_listed_digest_for_its_path_is_a_pre_move_copy():
    """A listed digest on the same path matches."""
    assert is_pre_move_copy({"tools/a.py": frozenset({K_ABC})}, "tools/a.py", "abc")


def test_a_digest_listed_for_another_path_or_for_another_body_is_no_pre_move_copy():
    """Neither a digest of another path nor an unlisted body matches."""
    digests = {"tools/a.py": frozenset({K_ABC})}
    assert not is_pre_move_copy(digests, "tools/b.py", "abc")
    assert not is_pre_move_copy(digests, "tools/a.py", "abd")


def test_the_reader_returns_the_digests_of_each_path(tmp_path):
    """One table per path becomes one set per path."""
    source = tmp_path / "d.toml"
    source.write_text(f'format_version = 1\n\n[files."tools/a.py"]\ndigests = ["{K_ABC}"]\n', encoding="utf-8")
    assert read_pre_move_digests(source) == {"tools/a.py": frozenset({K_ABC})}


def test_the_reader_refuses_a_newer_format_version(tmp_path):
    """A version the reader does not know is rejected, naming both versions."""
    source = tmp_path / "d.toml"
    source.write_text("format_version = 2\n", encoding="utf-8")
    with pytest.raises(SharedToolsError, match="version 2.*knows 1"):
        read_pre_move_digests(source)


def test_the_reader_refuses_a_missing_file(tmp_path):
    """A file that is not there is no digest file."""
    with pytest.raises(SharedToolsError):
        read_pre_move_digests(tmp_path / "none.toml")


def test_the_frozen_file_ships_in_the_package_folder_and_holds_digests():
    """The data file beside the code is readable and non-empty."""
    assert K_DIGESTS_PATH.is_file()
    assert read_pre_move_digests()
