# test_junit_report.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests writing the JUnit file of a run the command made itself."""

import pytest

from sushicore.testing.junit_report import junit_text
from sushicore.testing.result_files import failed_tests

pytestmark = pytest.mark.small


def test_a_test_with_an_exit_code_other_than_zero_is_a_failed_case_the_reader_finds():
    text = junit_text({"core.small_shard_0of2": 0, 'core.<odd>"': 3})
    assert failed_tests(text) == ('core.<odd>"',)


def test_a_run_of_no_tests_is_a_file_with_no_failure():
    assert failed_tests(junit_text({})) == ()
