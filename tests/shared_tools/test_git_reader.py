# test_git_reader.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the git reader on a tagged checkout."""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner
from sushicore.quiet_runner import quiet_runner
from sushicore.shared_tools import GitReader, SharedToolsError, TagNotFoundError
from sushicore.shared_tools.git_reader import tracked_files

from .conftest import K_SHARED, K_TAG

pytestmark = pytest.mark.medium


def test_commit_is_the_hash_of_the_tag(upstream):
    """A known tag names a 40 character commit."""
    assert len(GitReader(upstream).commit(K_TAG)) == 40


def test_an_unknown_tag_raises(upstream):
    """A tag the checkout lacks is TagNotFoundError."""
    with pytest.raises(TagNotFoundError):
        GitReader(upstream).commit("v9.9.9")


def test_show_reads_the_committed_text_and_none_for_a_missing_path(upstream):
    """A path of the tag gives its text; any other gives None."""
    reader = GitReader(upstream)
    assert reader.show(K_TAG, K_SHARED) == (upstream / K_SHARED).read_text(encoding="utf-8").replace("\r\n", "\n")
    assert reader.show(K_TAG, "tools/none.py") is None


def test_snapshot_gives_each_file_below_the_prefixes_as_show_gives_it(upstream):
    """One read returns the texts `show` returns, for the prefixes and no other path."""
    reader = GitReader(upstream)
    texts = reader.snapshot(K_TAG, "tools", ".github")
    listed = reader.files(K_TAG, "tools", ".github")
    assert texts == {path: reader.show(K_TAG, path) for path in listed}


def test_snapshot_leaves_out_a_path_below_no_prefix(upstream):
    """A file of the tag that no prefix names is not read."""
    texts = GitReader(upstream).snapshot(K_TAG, ".github")
    assert set(texts) == {".github/SECURITY.md"}


def test_snapshot_asks_git_once_however_many_files_the_tag_holds(upstream):
    """The tag is archived in one call, so the cost does not grow with the file count."""
    asked: list[list[str]] = []
    real = quiet_runner()

    class Counting:
        """Passes every command to the real runner and records it."""

        def capture_bytes(self, cmd, cwd=None, env=None, timeout=None):
            asked.append(cmd)
            return real.capture_bytes(cmd, cwd, env, timeout)

    GitReader(upstream, Counting()).snapshot(K_TAG, "tools", ".github")
    assert [command[3] for command in asked] == ["archive"]


def test_snapshot_of_a_tag_git_cannot_archive_raises(upstream):
    """A git that exits non-zero is an error, not an empty snapshot."""
    reader = GitReader(Path("repo"), RecordingRunner(RecordingConsole()).script(128))
    with pytest.raises(SharedToolsError):
        reader.snapshot(K_TAG, "tools")


def test_extract_unpacks_where_tarfile_has_no_extraction_filter(upstream, tmp_path, monkeypatch):
    """A Python before the extraction filters still unpacks the tag's folder."""
    original = tarfile.TarFile.extractall

    def without_filter(self, path=".", members=None, *, numeric_owner=False):
        return original(self, path, members, numeric_owner=numeric_owner, filter="fully_trusted")

    monkeypatch.setattr(tarfile.TarFile, "extractall", without_filter)
    monkeypatch.delattr(tarfile, "data_filter", raising=False)
    GitReader(upstream).extract(K_TAG, "tools", tmp_path)
    assert (tmp_path / K_SHARED).is_file()


def test_files_lists_the_tag_under_the_given_paths(upstream):
    """The listing holds the shared tools and the community file."""
    assert {K_SHARED, ".github/SECURITY.md"} <= set(GitReader(upstream).files(K_TAG, "tools", ".github"))


def test_tracked_files_of_a_folder_that_is_no_repository_is_empty(tmp_path):
    """A folder outside git tracks nothing."""
    assert tracked_files(tmp_path, "tools") == []


def test_tracked_files_lists_what_the_runner_reports_for_git():
    """Each line git prints is one tracked file, asked for under the given paths."""
    runner = RecordingRunner(RecordingConsole()).script(0, ("tools/a.py", "tools/b.py"))
    assert tracked_files(Path("repo"), "tools", runner=runner) == ["tools/a.py", "tools/b.py"]
    assert [c.argv for c in runner.commands] == [
        ("git", "-C", "repo", "ls-files", "--", "tools")]


def test_a_reader_whose_git_fails_finds_no_commit_for_the_tag():
    """A git that exits non-zero is a missing tag, not a crash."""
    reader = GitReader(Path("repo"), RecordingRunner(RecordingConsole()).script(128))
    with pytest.raises(TagNotFoundError):
        reader.commit(K_TAG)
