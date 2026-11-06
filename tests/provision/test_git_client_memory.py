# test_git_client_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the in-memory git client promises beyond the git client contract in test_git_client.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.git_client_memory import InMemoryGitClient

pytestmark = pytest.mark.small

K_ROOT = Path("checkouts")


def test_a_clone_is_recorded_with_its_url_tag_destination_and_dry_run_flag():
    git = InMemoryGitClient(commit="ab" * 20)
    git.clone_tag("https://x/y.git", "v1", K_ROOT / "y", False)
    assert git.calls == [("https://x/y.git", "v1", K_ROOT / "y", False)]


def test_a_tag_outside_the_table_lands_on_the_fallback_commit():
    git = InMemoryGitClient(commit="cd" * 20)
    git.clone_tag("https://x/y.git", "v2", K_ROOT / "y", False)
    assert git.head(K_ROOT / "y") == "cd" * 20


def test_a_tag_in_the_table_lands_on_its_own_commit_not_the_fallback():
    git = InMemoryGitClient({("https://x/y.git", "v1"): "ab" * 20}, commit="cd" * 20)
    git.clone_tag("https://x/y.git", "v1", K_ROOT / "y", False)
    assert git.head(K_ROOT / "y") == "ab" * 20


def test_a_client_built_not_to_clone_fails_every_clone():
    git = InMemoryGitClient(commit="ab" * 20, clones=False)
    assert git.clone_tag("https://x/y.git", "v1", K_ROOT / "y", False) is False


def test_a_clone_writes_nothing_unless_it_is_asked_to_materialize():
    InMemoryGitClient(commit="ab" * 20).clone_tag("https://x/y.git", "v1", K_ROOT / "y", False)
    assert not (K_ROOT / "y").exists()


def test_a_successful_clone_hands_its_destination_to_materialize():
    made = []
    git = InMemoryGitClient(commit="ab" * 20, materialize=made.append)
    git.clone_tag("https://x/y.git", "v1", K_ROOT / "y", False)
    assert made == [K_ROOT / "y"]


def test_a_failed_or_dry_run_clone_is_not_materialized():
    made = []
    InMemoryGitClient(clones=False, materialize=made.append).clone_tag(
        "https://x/y.git", "v1", K_ROOT / "a", False)
    InMemoryGitClient(commit="ab" * 20, materialize=made.append).clone_tag(
        "https://x/y.git", "v1", K_ROOT / "b", True)
    assert made == []


def test_a_failed_clone_is_still_recorded():
    git = InMemoryGitClient(clones=False)
    git.clone_tag("https://x/y.git", "v1", K_ROOT / "y", False)
    assert len(git.calls) == 1


def test_the_head_of_a_listed_checkout_is_the_one_given():
    git = InMemoryGitClient(heads={K_ROOT: "ab" * 20})
    assert git.head(K_ROOT) == "ab" * 20


def test_the_head_of_an_unlisted_checkout_is_the_default_head():
    assert InMemoryGitClient(default_head="ef" * 20).head(K_ROOT) == "ef" * 20


def test_a_head_is_returned_in_lower_case():
    assert InMemoryGitClient(heads={K_ROOT: "ABCDEF"}).head(K_ROOT) == "abcdef"
