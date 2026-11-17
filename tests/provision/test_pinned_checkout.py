# test_pinned_checkout.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A clone is accepted only when git's HEAD is the commit its entry pins."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.errors import CommitMismatchError
from sushicore.fragment_types import GitPin
from sushicore.provision.git_client_memory import InMemoryGitClient
from sushicore.provision.pinned_checkout import checkout_pinned, verify_checkout

pytestmark = pytest.mark.small

K_COMMIT = "7677cf6eefd8ab46d66168cd07ab042109448124"
K_OTHER = "0123456789abcdef0123456789abcdef01234567"
K_PIN = GitPin("acpp", "v24.10.0", K_COMMIT)
K_URL = "https://example.invalid/acpp.git"


def test_a_checkout_that_lands_on_the_pin_is_accepted():
    """Check that the fetch names the pinned hash and a matching HEAD passes."""
    git = InMemoryGitClient()

    assert checkout_pinned(git, K_URL, K_PIN, Path("acpp"), False) is True
    assert git.checkouts == [(K_URL, K_COMMIT, Path("acpp"), False, True)]


def test_a_checkout_that_lands_elsewhere_is_refused_with_both_commits():
    """Check that a HEAD other than the pin raises an error naming the pin and the HEAD."""
    git = InMemoryGitClient(checkout_head=K_OTHER)

    with pytest.raises(CommitMismatchError) as caught:
        checkout_pinned(git, K_URL, K_PIN, Path("acpp"), False)

    assert (caught.value.expected, caught.value.actual) == (K_COMMIT, K_OTHER)
    assert K_COMMIT in str(caught.value) and K_OTHER in str(caught.value)


def test_a_head_git_cannot_read_is_a_mismatch():
    """Check that an unreadable HEAD is refused, never taken as the pin."""
    git = InMemoryGitClient(default_head="")

    with pytest.raises(CommitMismatchError, match="no readable commit"):
        verify_checkout(git, Path("elsewhere"), K_PIN)


def test_a_failed_fetch_answers_false_and_reads_no_head():
    """Check that a fetch that fails is a False answer, not a mismatch."""
    git = InMemoryGitClient(clones=False)

    assert checkout_pinned(git, K_URL, K_PIN, Path("acpp"), False) is False


def test_a_dry_run_reads_no_head():
    """Check that a dry run passes without confirming a HEAD nothing fetched."""
    git = InMemoryGitClient(checkout_head=K_OTHER)

    assert checkout_pinned(git, K_URL, K_PIN, Path("acpp"), True) is True
