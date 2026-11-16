# program_cases.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tells which test program holds a suite a case filter can reach, from the listing the last run left."""

from __future__ import annotations

import json
from pathlib import Path

from ..files import Files
from .gtest_filter import intersect_filters
from .shards import program_executable

def executable_modified_time(files: Files, path: Path) -> float | None:
    """Return the modification time of *path*, or of *path* with ``.exe`` when only that is known.

    None when neither is known.
    """
    for candidate in (path, path.with_name(path.name + ".exe")):
        seconds = files.modified_time(candidate)
        if seconds is not None:
            return seconds
    return None


def listing_is_current(listing_time: float | None, program_time: float | None) -> bool:
    """Return whether a listing written at *listing_time* describes a program built at *program_time*.

    A time that is not known cannot show it, so the listing is not current then.
    """
    return listing_time is not None and program_time is not None and program_time <= listing_time


def programs_file(tree: Path) -> Path:
    """Return the file that maps each suite of the last run to the program that holds it."""
    return tree / "Testing" / "programs.json"


def suites_by_program(tree: Path, files: Files) -> dict[str, frozenset[str]]:
    """Return the suites each program held in the last run, read from ``programs.json``.

    A program the listing does not name, a missing file, a file that is not a map of text to text and a
    program whose executable is newer than the listing, or whose time cannot be read, all give no
    entry, so the caller treats that program as unknown.
    """
    listing = programs_file(tree)
    if not files.is_file(listing):
        return {}
    try:
        suite_to_program = json.loads(files.read_text(listing))
    except ValueError:
        return {}
    if not isinstance(suite_to_program, dict):
        return {}
    suites: dict[str, set[str]] = {}
    for suite, program in suite_to_program.items():
        if isinstance(suite, str) and isinstance(program, str):
            suites.setdefault(program, set()).add(suite)
    listing_time = files.modified_time(listing)
    return {program: frozenset(names) for program, names in suites.items()
            if _is_current_for(program, tree, files, listing_time)}


def _is_current_for(program: str, tree: Path, files: Files, listing_time: float | None) -> bool:
    """Return whether the listing is current for *program*, by the time of its executable."""
    executable = program_executable(tree, program, files)
    return executable is not None and listing_is_current(listing_time, executable_modified_time(files, executable))


def may_hold_a_case(suites: frozenset[str] | None, user_filter: str) -> bool:
    """Return whether a program with the given *suites* can hold a case *user_filter* selects.

    A program whose suites are not known (None or empty) may hold one, so it is never skipped on
    missing data. A key is a whole suite name or one ``/`` part of it, and a part only adds a pattern
    that selects nothing more than its whole suite does.
    """
    if not suites:
        return True
    return any(intersect_filters(pattern, user_filter) is not None
               for key in suites for pattern in (f"{key}.*",))
