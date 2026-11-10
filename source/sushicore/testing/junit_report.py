# junit_report.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Writes the JUnit text of a run the command made itself, in the shape CTest's file has."""

from __future__ import annotations

from collections.abc import Mapping
from xml.sax.saxutils import quoteattr


def junit_text(exit_codes: Mapping[str, int]) -> str:
    """Return a JUnit file with one test case per test, failed when its exit code is not 0.

    Args:
        exit_codes: The exit code of each test by its CTest name.
    """
    cases = "".join(
        f"<testcase name={quoteattr(name)} status={quoteattr('run' if code == 0 else 'fail')}>"
        + ("" if code == 0 else f"<failure message={quoteattr(f'exit {code}')}/>") + "</testcase>"
        for name, code in exit_codes.items())
    failures = sum(1 for code in exit_codes.values() if code != 0)
    return (f'<?xml version="1.0" encoding="UTF-8"?><testsuite name="shards" tests="{len(exit_codes)}" '
            f'failures="{failures}">{cases}</testsuite>')
