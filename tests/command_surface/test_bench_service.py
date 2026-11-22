# test_bench_service.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a bench request describes the plain bench by default and cannot be changed."""

import dataclasses

import pytest

from sushicore.command_surface import BenchRequest

pytestmark = pytest.mark.small


def test_bench_request_with_a_type_alone_carries_no_option_of_the_cli():
    assert BenchRequest("release").extra == {}


def test_bench_request_cannot_be_changed_by_the_service():
    request = BenchRequest(build_type="release")
    with pytest.raises(dataclasses.FrozenInstanceError):
        request.extra = {"report": True}
