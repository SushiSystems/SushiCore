# test_check.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the contract one diagnostic implements."""

from __future__ import annotations

import pytest

from sushicore.provision.check import Check
from sushicore.provision.check_result import CheckResult
from sushicore.provision.check_state import State


class _Fixed:
    """A diagnostic that satisfies the contract without inheriting from it."""

    name = "fixed"
    group = "build"
    required = True

    def run(self) -> CheckResult:
        """Report success."""
        return CheckResult(State.OK, "fixed")


@pytest.mark.small
def test_a_class_with_the_contract_members_is_a_check():
    """Check that the contract is structural: a plain class with its members passes as a Check."""
    check: Check = _Fixed()
    assert check.run().state is State.OK
