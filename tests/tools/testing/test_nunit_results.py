# test_nunit_results.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests how the times and sizes of an NUnit 3 results file are read."""

from __future__ import annotations

import unittest
import xml.etree.ElementTree as ElementTree


from sushicore.tools.testing.nunit_results import parse_nunit  # noqa: E402
from sushicore.tools.testing.timing import Timing  # noqa: E402


def _category(name: str) -> str:
    """Returns the properties element that gives its owner a category."""
    return f'<properties><property name="Category" value="{name}"/></properties>'


def _run(body: str) -> list[Timing]:
    """Returns what the reader makes of a `test-run` holding the body."""
    return parse_nunit(ElementTree.fromstring(f"<test-run>{body}</test-run>"))


class NunitResultsTest(unittest.TestCase):
    """Covers sizes, names, durations and skipped tests of an NUnit 3 `test-run`."""
    K_TEST_SIZE = "small"

    def test_a_test_takes_the_size_of_its_fixture(self) -> None:
        body = (f'<test-suite>{_category("small")}'
                '<test-case fullname="G.Shape.One" duration="0.25" classname="G.Shape"/></test-suite>')
        self.assertEqual(_run(body), [Timing("G.Shape.One", 0.25, "small", "G.Shape")])

    def test_the_category_of_a_test_beats_the_one_of_its_fixture(self) -> None:
        body = (f'<test-suite>{_category("small")}'
                f'<test-case fullname="G.Shape.One" duration="2" classname="G.Shape">{_category("medium")}</test-case>'
                "</test-suite>")
        self.assertEqual(_run(body)[0].size, "medium")

    def test_the_nearest_suite_above_a_test_gives_its_size(self) -> None:
        body = (f'<test-suite>{_category("large")}<test-suite>{_category("small")}'
                '<test-case fullname="G.Shape.One" duration="1" classname="G.Shape"/></test-suite></test-suite>')
        self.assertEqual(_run(body)[0].size, "small")

    def test_a_suite_without_a_category_inherits_the_size_above_it(self) -> None:
        body = (f'<test-suite>{_category("medium")}<test-suite>'
                '<test-case fullname="G.Shape.One" duration="1" classname="G.Shape"/></test-suite></test-suite>')
        self.assertEqual(_run(body)[0].size, "medium")

    def test_a_test_with_no_category_anywhere_has_no_size(self) -> None:
        body = '<test-suite><test-case fullname="G.Shape.One" duration="1" classname="G.Shape"/></test-suite>'
        self.assertIsNone(_run(body)[0].size)

    def test_a_benchmark_has_no_size_whatever_its_fixture_gives(self) -> None:
        body = (f'<test-suite>{_category("small")}'
                f'<test-case fullname="G.Shape.Bench" duration="9" classname="G.Shape">{_category("benchmark")}</test-case>'
                "</test-suite>")
        self.assertIsNone(_run(body)[0].size)

    def test_a_skipped_test_is_left_out(self) -> None:
        body = ('<test-suite><test-case fullname="G.A.Gone" result="Skipped" duration="0" classname="G.A"/>'
                '<test-case fullname="G.A.Ran" result="Passed" duration="1" classname="G.A"/></test-suite>')
        self.assertEqual([timing.name for timing in _run(body)], ["G.A.Ran"])

    def test_a_missing_or_empty_duration_counts_as_zero_seconds(self) -> None:
        body = ('<test-case fullname="G.A.One" classname="G.A"/>'
                '<test-case fullname="G.A.Two" duration="" classname="G.A"/>')
        self.assertEqual([timing.seconds for timing in _run(body)], [0.0, 0.0])

    def test_a_case_without_a_fullname_is_named_by_its_name(self) -> None:
        self.assertEqual(_run('<test-case name="Plain" duration="1"/>')[0].name, "Plain")

    def test_cases_that_share_a_set_name_are_told_apart_by_their_method(self) -> None:
        body = ('<test-case fullname="G.A.Rows(1)" methodname="Rows" name="Rows(1)" classname="G.A" duration="1"/>'
                '<test-case fullname="G.A.Set" methodname="Rows" name="Set" classname="G.A" duration="1"/>')
        self.assertEqual([timing.name for timing in _run(body)], ["G.A.Rows(1)", "G.A.Rows.Set"])

    def test_the_suite_of_a_timing_is_the_class_of_its_case(self) -> None:
        self.assertEqual(_run('<test-case fullname="G.A.One" classname="G.A" duration="1"/>')[0].suite, "G.A")

    def test_a_run_without_cases_has_no_timings(self) -> None:
        self.assertEqual(_run("<test-suite/>"), [])


if __name__ == "__main__":
    unittest.main()
