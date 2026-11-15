# test_git_reader.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the git reader on a tagged checkout."""

from __future__ import annotations

import pytest

from sushicore.shared_tools import GitReader, TagNotFoundError
from sushicore.shared_tools.git_reader import tracked_files

from .conftest import K_SHARED, K_TAG

pytestmark = pytest.mark.medium


def test_commit_is_the_hash_of_the_tag(upstream):
    """A known tag names a 40 character commit."""
    assert len(GitReader(upstream).commit(K_TAG)) == 40


def test_an_unknown_tag_raises(upstream):
    """A tag the checkout lacks is TagNotFoundError."""
    with pytest.raises(TagNotFoundError):
        GitReader(upstream).commit("v9.9.9")


def test_show_reads_the_committed_text_and_none_for_a_missing_path(upstream):
    """A path of the tag gives its text; any other gives None."""
    reader = GitReader(upstream)
    assert reader.show(K_TAG, K_SHARED) == (upstream / K_SHARED).read_text(encoding="utf-8").replace("\r\n", "\n")
    assert reader.show(K_TAG, "tools/none.py") is None


def test_files_lists_the_tag_under_the_given_paths(upstream):
    """The listing holds the shared tools and the community file."""
    assert {K_SHARED, ".github/SECURITY.md"} <= set(GitReader(upstream).files(K_TAG, "tools", ".github"))


def test_tracked_files_of_a_folder_that_is_no_repository_is_empty(tmp_path):
    """A folder outside git tracks nothing."""
    assert tracked_files(tmp_path, "tools") == []
