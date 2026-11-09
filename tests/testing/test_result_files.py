# test_result_files.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests reading the failing tests and cases out of CTest's JUnit and GoogleTest's XML."""

import pytest

from sushicore.testing.result_files import ResultFileError, failed_tests, failing_cases

pytestmark = pytest.mark.small

K_JUNIT = (
    '<?xml version="1.0"?><testsuite>'
    '<testcase name="core.small_shard_0of2" status="run"/>'
    '<testcase name="core.small_shard_1of2" status="fail"><failure message="Failed"/></testcase>'
    '<testcase name="core.medium_shard_0of1" status="notrun"/>'
    "</testsuite>")

K_GTEST = (
    '<?xml version="1.0"?><testsuites><testsuite name="S">'
    '<testcase name="Ok" status="run" classname="Small_A"/>'
    '<testcase name="Bad" status="run" classname="Small_A"><failure message="x"/></testcase>'
    '<testcase name="Row/3" status="run" classname="Rows/Medium_B"><failure message="y"/></testcase>'
    "</testsuite></testsuites>")


def test_failed_tests_names_the_ctest_tests_that_failed_and_not_the_ones_not_run():
    assert failed_tests(K_JUNIT) == ("core.small_shard_1of2",)


def test_failing_cases_names_each_failing_case_as_a_filter_pattern():
    assert failing_cases(K_GTEST) == ("Small_A.Bad", "Rows/Medium_B.Row/3")


@pytest.mark.parametrize("text", [
    '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><testsuite/>',
    "not xml at all",
])
def test_a_result_file_that_declares_an_entity_or_is_not_xml_is_refused(text):
    with pytest.raises(ResultFileError):
        failing_cases(text)
