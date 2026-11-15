# test_errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the errors the shared tools commands report."""

from __future__ import annotations

import pytest

from sushicore.errors import SushiCoreError
from sushicore.shared_tools import (
    CheckoutNotFoundError,
    LocalEditsError,
    NoLockError,
    SharedToolsError,
    TagNotFoundError,
)

pytestmark = pytest.mark.small


@pytest.mark.parametrize("kind", [CheckoutNotFoundError, LocalEditsError, NoLockError, TagNotFoundError])
def test_every_error_reaches_the_entry_point_as_a_sushicore_error(kind):
    """The entry point of the CLI catches each one and prints it as one line."""
    assert issubclass(kind, SharedToolsError)
    assert issubclass(kind, SushiCoreError)


def test_local_edits_name_their_files():
    """The message lists the files."""
    assert str(LocalEditsError(["a", "b"])) == "a, b"
