# test_pre_move_digest_writer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the writer of the frozen digest file on a throwaway clone with two versions of one file."""

from __future__ import annotations

import hashlib

import pytest

from sushicore.shared_tools import GitReader
from sushicore.shared_tools.pre_move_digest_writer import collect_digests, render
from sushicore.shared_tools.pre_move_digests import read_pre_move_digests

from .conftest import git

pytestmark = pytest.mark.medium

K_PATH = "tools/a.py"


def _sha(text: str) -> str:
    """Returns the SHA-256 hex of a text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture()
def skills(tmp_path):
    """Returns a clone whose history holds two versions of one file."""
    folder = tmp_path / "skills"
    (folder / "tools").mkdir(parents=True)
    git(tmp_path, "init", "-q", str(folder))
    for text in ("one\n", "two\n"):
        (folder / K_PATH).write_text(text, encoding="utf-8")
        git(folder, "add", "-A")
        git(folder, "commit", "-q", "-m", text.strip())
    return folder


def test_every_committed_version_of_a_path_is_hashed_and_a_path_without_history_is_left_out(skills):
    """Both versions give a digest, sorted; a path never committed gives none."""
    found = collect_digests(GitReader(skills), [K_PATH, "tools/none.py"], lambda path, text: text)
    assert found == {K_PATH: sorted([_sha("one\n"), _sha("two\n")])}


def test_the_body_function_decides_what_is_hashed(skills):
    """A body function that drops the first line makes the two versions hash alike."""
    found = collect_digests(GitReader(skills), [K_PATH], lambda path, text: "same\n")
    assert found == {K_PATH: [_sha("same\n")]}


def test_the_rendered_file_reads_back_to_the_digests_and_lists_paths_in_order(tmp_path):
    """Rendering then reading returns the same sets, with the tables sorted by path."""
    digests = {"tools/b.py": [_sha("b")], "tools/a.py": [_sha("a2"), _sha("a1")]}
    text = render(digests)
    target = tmp_path / "d.toml"
    target.write_text(text, encoding="utf-8")
    assert read_pre_move_digests(target) == {path: frozenset(rows) for path, rows in digests.items()}
    assert text.index("tools/a.py") < text.index("tools/b.py")
