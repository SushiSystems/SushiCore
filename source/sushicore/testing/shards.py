# shards.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Names the shards a build registers and where a run leaves their results."""

from __future__ import annotations

import re
from pathlib import Path

from ..files import Files

#: A CTest test registered as a shard: ``<program>.<size>_shard_<index>of<count>``.
K_SHARD_NAME = re.compile(r"^(?P<program>.+)\.[a-z]+_shard_\d+of\d+$")

#: The shard part of a name inside a CTest test file.
_K_SHARD_REGISTRATION = re.compile(r"\.[a-z]+_shard_\d+of\d+")

#: A ``subdirs`` call of a generated CTest test file, its folder in quotes or bare.
_K_SUBDIRS = re.compile(r'subdirs\(\s*"?([^"\s)]+)"?')

#: The test file CMake writes into every folder of a build tree that holds tests.
K_TEST_FILE = "CTestTestfile.cmake"


def program_of(test_name: str) -> str | None:
    """Return the test program a shard runs, or None when *test_name* is not a shard."""
    found = K_SHARD_NAME.match(test_name)
    return found.group("program") if found else None


def gtest_results_folder(tree: Path) -> Path:
    """Return the folder the shards of a run write their GoogleTest XML into."""
    return tree / "test_results" / "gtest"


def rerun_results_folder(tree: Path) -> Path:
    """Return the folder the rerun of failed shard cases writes its GoogleTest XML into."""
    return tree / "test_results" / "rerun"


def registers_shards(tree: Path, files: Files) -> bool:
    """Return whether any test file of the build tree registers a test as a shard.

    The walk follows the ``subdirs`` calls from the tree's own test file, so it reads only the
    folders CMake generated test files for.
    """
    pending = [tree]
    seen: set[Path] = set()
    while pending:
        folder = pending.pop()
        test_file = folder / K_TEST_FILE
        if folder in seen or not files.is_file(test_file):
            continue
        seen.add(folder)
        text = files.read_text(test_file)
        if _K_SHARD_REGISTRATION.search(text):
            return True
        pending.extend(folder / child for child in _K_SUBDIRS.findall(text))
    return False
