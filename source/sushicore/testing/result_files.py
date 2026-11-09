# result_files.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads the failing tests out of the result files a run leaves: CTest's JUnit and GoogleTest's XML."""

from __future__ import annotations

from xml.etree import ElementTree


class ResultFileError(Exception):
    """Raised when a result file cannot be read as the XML a test run writes."""


def failed_tests(junit_text: str) -> tuple[str, ...]:
    """Return the names of the CTest tests that failed in a JUnit file, in file order.

    A test that was not run is not a failure and is left out.

    Args:
        junit_text: The text of the file ``ctest --output-junit`` wrote.

    Raises:
        ResultFileError: When the text is not XML or declares a DOCTYPE or an ENTITY.
    """
    return tuple(case.get("name", "") for case in _root(junit_text).iter("testcase") if _failed(case))


def failing_cases(gtest_text: str) -> tuple[str, ...]:
    """Return the ``Suite.Case`` names that failed in a GoogleTest XML file, in file order.

    A parametrised case keeps its instantiation prefix and its ``/index``, so the name is a
    ``--gtest_filter`` pattern that selects exactly that case.

    Args:
        gtest_text: The text of a file ``--gtest_output=xml:`` wrote.

    Raises:
        ResultFileError: When the text is not XML or declares a DOCTYPE or an ENTITY.
    """
    return tuple(f"{case.get('classname', '')}.{case.get('name', '')}"
                 for case in _root(gtest_text).iter("testcase") if _failed(case))


def _failed(case: ElementTree.Element) -> bool:
    """Return whether a test case carries a failure or an error."""
    return case.find("failure") is not None or case.find("error") is not None or case.get("status") == "fail"


def _root(text: str) -> ElementTree.Element:
    """Return the root of an XML result file; one with a DOCTYPE or an ENTITY is refused unread.

    CTest and GoogleTest write neither, and the standard library parser expands them.
    """
    if "<!DOCTYPE" in text or "<!ENTITY" in text:
        raise ResultFileError("a test result file has no DOCTYPE or ENTITY; refusing to parse it")
    try:
        return ElementTree.fromstring(text)
    except ElementTree.ParseError as error:
        raise ResultFileError(f"a test result file is not XML: {error}") from error
