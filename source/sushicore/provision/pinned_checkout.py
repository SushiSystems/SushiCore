# pinned_checkout.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Checks out a clone at the commit its manifest entry pins and confirms git's HEAD is that commit."""

from __future__ import annotations

from pathlib import Path

from sushicore.errors import CommitMismatchError
from sushicore.fragment_types import GitPin

from .git_client import IGitClient


def verify_checkout(git: IGitClient, destination: Path, pin: GitPin) -> None:
    """Check that the HEAD of *destination* is the commit *pin* names.

    Raises:
        CommitMismatchError: HEAD is another commit, or git could not read it.
    """
    actual = git.head(destination)
    if actual != pin.commit:
        raise CommitMismatchError(f"The checkout {destination}", pin.commit, actual)


def checkout_pinned(git: IGitClient, url: str, pin: GitPin, destination: Path, dry_run: bool,
                    *, shallow: bool = True) -> bool:
    """Fetch *url* at the commit of *pin* into *destination* and confirm HEAD is that commit.

    Args:
        shallow: Fetch the one commit without its history.

    Returns:
        False when git could not fetch or check out; the checkout is confirmed otherwise.

    Raises:
        CommitMismatchError: The checkout ended at another commit.
    """
    if not git.checkout_commit(url, pin.commit, destination, dry_run, shallow=shallow):
        return False
    if not dry_run:
        verify_checkout(git, destination, pin)
    return True
