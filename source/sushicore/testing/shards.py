# shards.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Names the shards a build registers and where a run leaves their results."""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from ..files import Files

#: A CTest test registered as a shard, ``<program>.<size>_shard_<index>of<count>`` or ``<program>.<size>_quarantined``.
K_SHARD_NAME = re.compile(r"^(?P<program>.+)\.[a-z]+_(?:shard_\d+of\d+|quarantined)$")

#: The shard part of a name inside a CTest test file.
_K_SHARD_REGISTRATION = re.compile(r"\.[a-z]+_shard_\d+of\d+")

#: An ``add_test`` call of a generated CTest test file: the test's name and the executable it runs.
_K_ADD_TEST = re.compile(r'add_test\(\[=\[(?P<name>[^\]]+)\]=\]\s+"(?P<executable>[^"]+)"')

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


def test_file_texts(tree: Path, files: Files) -> Iterator[str]:
    """Yield the text of each test file of the build tree, following the ``subdirs`` calls from its own.

    The walk reads only the folders CMake generated test files for.
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
        yield text
        pending.extend(folder / child for child in _K_SUBDIRS.findall(text))


def registers_shards(tree: Path, files: Files) -> bool:
    """Return whether any test file of the build tree registers a test as a shard."""
    return any(_K_SHARD_REGISTRATION.search(text) for text in test_file_texts(tree, files))


def program_executable(tree: Path, program: str, files: Files) -> Path | None:
    """Return the executable the shards of *program* run, or None when the tree registers none."""
    for text in test_file_texts(tree, files):
        for registration in _K_ADD_TEST.finditer(text):
            if program_of(registration.group("name")) == program:
                return Path(registration.group("executable"))
    return None
