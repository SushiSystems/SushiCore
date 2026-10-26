# test_source_state.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the source hash of a library checkout."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.source_state import describe_source, is_excluded

pytestmark = pytest.mark.medium


class _Files:
    """Lists the files of a folder, as a git checkout with nothing ignored would."""

    def files(self, checkout: Path) -> list[Path]:
        """Return every file below *checkout*, relative to it."""
        return sorted(p.relative_to(checkout) for p in checkout.rglob("*") if p.is_file())


class _NotARepository:
    """Raises the error a folder that is not a repository raises."""

    def files(self, checkout: Path) -> list[Path]:
        """Raise a package error."""
        raise PackageError(f"{checkout} is not a git checkout")


@pytest.fixture
def checkout(tmp_path):
    """Return a checkout with one source file, one page and one docs file."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.cpp").write_text("int a;", encoding="utf-8")
    (tmp_path / "README.md").write_text("one", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "x.txt").write_text("one", encoding="utf-8")
    return tmp_path


def _hash(checkout, excludes=()):
    """Return the source hash of *checkout*."""
    return describe_source(checkout, _Files(), excludes)


def test_a_change_under_docs_or_in_a_page_does_not_change_the_hash(checkout):
    """Check that docs/ and *.md leave the hash as it was."""
    before = _hash(checkout)
    (checkout / "README.md").write_text("two", encoding="utf-8")
    (checkout / "docs" / "x.txt").write_text("two", encoding="utf-8")
    (checkout / "docs" / "new.txt").write_text("new", encoding="utf-8")
    assert _hash(checkout) == before


def test_a_changed_source_file_changes_the_hash(checkout):
    """Check that editing a source file changes the hash."""
    before = _hash(checkout)
    (checkout / "src" / "a.cpp").write_text("int b;", encoding="utf-8")
    assert _hash(checkout) != before


def test_a_new_source_file_changes_the_hash(checkout):
    """Check that an untracked source file changes the hash."""
    before = _hash(checkout)
    (checkout / "src" / "b.cpp").write_text("", encoding="utf-8")
    assert _hash(checkout) != before


def test_a_deleted_file_changes_the_hash(checkout):
    """Check that a file removed from the working tree changes the hash."""
    before = _hash(checkout)
    (checkout / "src" / "a.cpp").unlink()
    assert _hash(checkout) != before


def test_the_build_folders_never_enter_the_hash(checkout):
    """Check that build/ and build-asan/ are left out whatever the ignore file says."""
    before = _hash(checkout)
    for folder in ("build", "build-asan"):
        (checkout / folder).mkdir()
        (checkout / folder / "obj.o").write_text("x", encoding="utf-8")
    assert _hash(checkout) == before


def test_a_package_exclude_entry_is_left_out(checkout):
    """Check that a folder prefix and a glob of package_exclude are left out."""
    (checkout / "bench").mkdir()
    (checkout / "bench" / "b.cpp").write_text("1", encoding="utf-8")
    (checkout / "notes.txt").write_text("1", encoding="utf-8")
    before = _hash(checkout, ("bench/", "*.txt"))
    (checkout / "bench" / "b.cpp").write_text("2", encoding="utf-8")
    (checkout / "notes.txt").write_text("2", encoding="utf-8")
    assert _hash(checkout, ("bench/", "*.txt")) == before


def test_a_folder_that_is_not_a_repository_raises(tmp_path):
    """Check that the error of the inspector reaches the caller."""
    with pytest.raises(PackageError, match="not a git checkout"):
        describe_source(tmp_path, _NotARepository())


@pytest.mark.parametrize("name, excluded", [
    ("docs/a.txt", True), ("build/x", True), ("build-asan/x", True), ("a.md", True),
    ("src/build/x", False), ("src/a.cpp", False), ("docs", False),
])
def test_the_built_in_exclusions(name, excluded):
    """Check which paths the built-in exclusions leave out."""
    assert is_excluded(Path(name), ()) is excluded
