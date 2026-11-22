# test_check_service.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a check request describes the plain check by default and cannot be changed."""

import dataclasses

import pytest

from sushicore.command_surface import CheckRequest

pytestmark = pytest.mark.small


def test_check_request_by_default_runs_every_rule_and_fails_on_a_finding():
    assert (CheckRequest().rule, CheckRequest().report) == (None, False)


def test_check_request_cannot_be_changed_by_the_service():
    request = CheckRequest()
    with pytest.raises(dataclasses.FrozenInstanceError):
        request.extra = {"report": True}
