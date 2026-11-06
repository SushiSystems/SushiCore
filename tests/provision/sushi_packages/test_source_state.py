# test_source_state.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the source hash of a library checkout."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.source_state import (
    GitSourceInspector,
    MemoryInspector,
    describe_source,
    is_excluded,
)


class _Source:
    """A checkout on disk and the inspector that lists its files, as git would."""

    def __init__(self, checkout: Path) -> None:
        """List the files the checkout starts with."""
        self.checkout = checkout
        self.inspector = MemoryInspector({checkout: []})
        for relative, text in (("src/a.cpp", "int a;"), ("README.md", "one"),
                               ("docs/x.txt", "one")):
            self.add(relative, text)

    def add(self, relative: str, text: str) -> None:
        """Write the file and list it."""
        self.write(relative, text)
        self.inspector.listing[self.checkout].append(Path(relative))

    def write(self, relative: str, text: str) -> None:
        """Write the file and leave the listing as it is."""
        path = self.checkout / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def hash(self, excludes=()) -> str:
        """Return the source hash of the checkout."""
        return describe_source(self.checkout, self.inspector, excludes)


@pytest.fixture
def source(tmp_path):
    """Return a checkout with one source file, one page and one docs file."""
    return _Source(tmp_path)


@pytest.mark.medium
def test_a_change_under_docs_or_in_a_page_does_not_change_the_hash(source):
    """Check that docs/ and *.md leave the hash as it was."""
    before = source.hash()
    source.write("README.md", "two")
    source.write("docs/x.txt", "two")
    source.add("docs/new.txt", "new")
    assert source.hash() == before


@pytest.mark.medium
def test_a_changed_source_file_changes_the_hash(source):
    """Check that editing a source file changes the hash."""
    before = source.hash()
    source.write("src/a.cpp", "int b;")
    assert source.hash() != before


@pytest.mark.medium
def test_a_new_source_file_changes_the_hash(source):
    """Check that an untracked source file changes the hash."""
    before = source.hash()
    source.add("src/b.cpp", "")
    assert source.hash() != before


@pytest.mark.medium
def test_a_deleted_file_changes_the_hash(source):
    """Check that a file git still lists but the working tree lost changes the hash."""
    before = source.hash()
    (source.checkout / "src" / "a.cpp").unlink()
    assert source.hash() != before


@pytest.mark.medium
def test_the_build_folders_never_enter_the_hash(source):
    """Check that build/ and build-asan/ are left out whatever the ignore file says."""
    before = source.hash()
    source.add("build/obj.o", "x")
    source.add("build-asan/obj.o", "x")
    assert source.hash() == before


@pytest.mark.medium
def test_a_package_exclude_entry_is_left_out(source):
    """Check that a folder prefix and a glob of package_exclude are left out."""
    source.add("bench/b.cpp", "1")
    source.add("notes.txt", "1")
    before = source.hash(("bench/", "*.txt"))
    source.write("bench/b.cpp", "2")
    source.write("notes.txt", "2")
    assert source.hash(("bench/", "*.txt")) == before


@pytest.mark.small
def test_a_folder_that_is_not_a_repository_raises():
    """Check that the error of the inspector reaches the caller."""
    with pytest.raises(PackageError, match="not a git checkout"):
        describe_source(Path("checkout"), MemoryInspector({}))


@pytest.mark.small
@pytest.mark.parametrize("name, excluded", [
    ("docs/a.txt", True), ("build/x", True), ("build-asan/x", True), ("a.md", True),
    ("src/build/x", False), ("src/a.cpp", False), ("docs", False),
])
def test_the_built_in_exclusions(name, excluded):
    """Check which paths the built-in exclusions leave out."""
    assert is_excluded(Path(name), ()) is excluded


@pytest.mark.medium
def test_git_lists_the_tracked_and_the_untracked_files_it_does_not_ignore(tmp_path):
    """Check that a tracked and an untracked file are listed, and an ignored one is not."""
    subprocess.run(["git", "-C", str(tmp_path), "init"], capture_output=True, check=True)
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "c.txt").write_text("c", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("c.txt\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "a.txt"], capture_output=True, check=True)
    listed = GitSourceInspector().files(tmp_path)
    assert listed == [Path(".gitignore"), Path("a.txt"), Path("b.txt")]


@pytest.mark.medium
def test_git_raises_for_a_folder_that_is_not_a_repository(tmp_path):
    """Check that a plain folder is refused as a checkout."""
    with pytest.raises(PackageError, match="not a git checkout"):
        GitSourceInspector().files(tmp_path)
