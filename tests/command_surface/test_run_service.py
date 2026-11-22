# test_run_service.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a run request describes the plain run by default and cannot be changed."""

import dataclasses

import pytest

from sushicore.command_surface import RunRequest

pytestmark = pytest.mark.small


def test_run_request_by_default_builds_first_and_forwards_nothing():
    assert (RunRequest().build, RunRequest().arguments, RunRequest().pick) == (True, (), False)


def test_run_request_cannot_be_changed_by_the_service():
    request = RunRequest()
    with pytest.raises(dataclasses.FrozenInstanceError):
        request.extra = {"report": True}
