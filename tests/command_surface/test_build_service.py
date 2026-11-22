# test_build_service.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a build request describes the plain build by default and cannot be changed."""

import dataclasses

import pytest

from sushicore.command_surface import BuildRequest

pytestmark = pytest.mark.small


def test_build_request_with_a_type_alone_builds_the_tests_with_no_sanitizer_define_or_job_count():
    request = BuildRequest("debug")
    assert (request.sanitizers, request.defines, request.jobs, request.tests) == ((), (), None, True)


def test_build_request_cannot_be_changed_by_the_service():
    request = BuildRequest(build_type="debug")
    with pytest.raises(dataclasses.FrozenInstanceError):
        request.extra = {"report": True}
