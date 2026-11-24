# test_timing.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the one shape every results reader of the time reader returns."""

from __future__ import annotations

import dataclasses
import unittest


from sushicore.tools.testing.timing import Timing  # noqa: E402


class TimingTest(unittest.TestCase):
    """Covers the values a timing holds and that it is a value."""
    K_TEST_SIZE = "small"

    def test_a_timing_without_a_size_or_a_suite_holds_neither(self) -> None:
        timing = Timing("A.One", 0.25)
        self.assertEqual((timing.name, timing.seconds, timing.size, timing.suite), ("A.One", 0.25, None, None))

    def test_two_timings_with_the_same_values_are_equal(self) -> None:
        self.assertEqual(Timing("A.One", 1.0, "small", "A"), Timing("A.One", 1.0, "small", "A"))

    def test_a_size_tells_two_timings_apart(self) -> None:
        self.assertNotEqual(Timing("A.One", 1.0, "small"), Timing("A.One", 1.0))

    def test_a_timing_cannot_be_changed(self) -> None:
        with self.assertRaises(dataclasses.FrozenInstanceError):
            Timing("A.One", 1.0).seconds = 2.0  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
