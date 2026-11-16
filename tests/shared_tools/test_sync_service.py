# test_sync_service.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the sync service on a tagged SushiCore checkout and a repository on disk."""

from __future__ import annotations

import hashlib
import shutil

import pytest

from sushicore.shared_tools import K_EXCLUDED, K_LOCK_PATH, GitReader, LocalEditsError, SharedToolsSync, read_lock

from .conftest import K_SHARED, K_TAG

pytestmark = pytest.mark.medium


def _sync(upstream, target, **options):
    """Runs a sync of the tag into the target."""
    return SharedToolsSync(GitReader(upstream), target, K_TAG, **options).run()


def test_sync_writes_the_files_and_the_lock(upstream, target):
    """The lock holds the tag, its commit and a hash for each shared file, and no SushiCore-only file."""
    result = _sync(upstream, target)
    lock = read_lock(target)
    assert lock.tag == K_TAG
    assert len(lock.commit) == 40
    assert K_SHARED in lock.files
    assert ".github/SECURITY.md" in lock.files
    assert not K_EXCLUDED.intersection(lock.files)
    assert K_SHARED in result.written
    assert lock.differing(target) == []


def test_a_local_edit_is_refused_and_nothing_else_is_written(upstream, target):
    """A file holding text no release held stops the sync before any write."""
    _sync(upstream, target)
    edited = target / K_SHARED
    edited.write_text(edited.read_text(encoding="utf-8") + "# mine\n", encoding="utf-8")
    shutil.rmtree(target / "tools" / "documentation")
    with pytest.raises(LocalEditsError) as refused:
        _sync(upstream, target)
    assert refused.value.files == [K_SHARED]
    assert "# mine" in edited.read_text(encoding="utf-8")
    assert not (target / "tools" / "documentation").exists()


def test_force_overwrites_a_local_edit(upstream, target):
    """With force the edited file is brought back to the tag."""
    _sync(upstream, target)
    edited = target / K_SHARED
    edited.write_text(edited.read_text(encoding="utf-8") + "# mine\n", encoding="utf-8")
    _sync(upstream, target, force=True)
    assert "# mine" not in edited.read_text(encoding="utf-8")


def test_kept_files_stay_as_the_repository_holds_them(upstream, target):
    """The settings and a kept file are untouched, the README keeps its text, and a kept file is not locked."""
    kept = "tools/ci/" + next((upstream / "tools" / "ci").iterdir()).name
    (target / kept).parent.mkdir(parents=True)
    (target / kept).write_text("my own\n", encoding="utf-8")
    _sync(upstream, target, keep=[kept])
    assert (target / "tools" / "settings.py").read_text(encoding="utf-8") == "K_OWN = 1\n"
    assert (target / "tools" / "README.md").read_text(encoding="utf-8").startswith("own readme\n")
    assert (target / kept).read_text(encoding="utf-8") == "my own\n"
    assert kept not in read_lock(target).files


def test_dry_run_writes_nothing(upstream, target):
    """A dry run lists the files and writes neither them nor the lock."""
    result = _sync(upstream, target, dry_run=True)
    assert K_SHARED in result.written
    assert not (target / K_SHARED).exists()
    assert not (target / K_LOCK_PATH).exists()


def test_the_checkers_of_sushicore_alone_are_left_out_of_the_shared_set() -> None:
    """The checkers that read SushiCore's own packages are not shared."""
    assert "tools/layering/check_package_layers.py" in K_EXCLUDED
    assert "tools/provision/check_config_reads.py" in K_EXCLUDED


K_NEW = "tools/documentation/check_changelog.py"
K_HELD = "tools/documentation/check_docs_layout.py"
K_CLOSED_SETTINGS = (
    "K_CLOSED = True\n"
    "K_LICENSE_HOLDER = 'Holder Ltd'\n"
    "K_LICENSE_COMPANY = 'Holder'\n"
    "K_LICENSE_OPEN_LINES = ('Licensed under the Open Licence.',)\n"
    "K_LICENSE_CLOSED_LINES = ('All rights reserved. No licence is granted.',)\n"
)
K_TEMPLATE_HEADER = "# check_all.py\n# Closed - https://example.com/closed\n# Copyright (c) 2021-present Holder Ltd\n# Licensed under the Open Licence.\n"
K_NEW_HEADER = (
    "# check_changelog.py\n# Closed - https://example.com/closed\n"
    "# Copyright (c) 2026-present Holder Ltd\n# All rights reserved. No licence is granted.\n"
)
K_HELD_HEADER = "# check_docs_layout.py\n# Closed - https://example.com/closed\n# Copyright (c) 2021-present Holder Ltd\n# Kept row.\n"


def _closed_target(target):
    """Makes the target a closed-licence repository holding one shared Python file and a template."""
    (target / "tools" / "settings.py").write_text(K_CLOSED_SETTINGS, encoding="utf-8")
    (target / "tools" / "check_all.py").write_text(K_TEMPLATE_HEADER + '"""Runs."""\n', encoding="utf-8")
    held = target / K_HELD
    held.parent.mkdir(parents=True)
    held.write_text(K_HELD_HEADER + '"""Old."""\n', encoding="utf-8")


def test_a_new_python_file_takes_the_header_the_targets_settings_build(upstream, target):
    """A closed-licence repository gets its own closed rows on a shared file it did not hold."""
    _closed_target(target)
    _sync(upstream, target, force=True)
    header = (target / K_NEW).read_text(encoding="utf-8").split('"""')[0]
    assert header == K_NEW_HEADER
    assert "Apache" not in header


def test_a_python_file_the_target_holds_keeps_its_header(upstream, target):
    """The header of a file the repository already holds is not rebuilt."""
    _closed_target(target)
    _sync(upstream, target, force=True)
    assert (target / K_HELD).read_text(encoding="utf-8").startswith(K_HELD_HEADER)


def test_sync_writes_the_shared_rows_into_the_readme_and_keeps_the_own_rows(upstream, target):
    """The README gains a row for a shared tool and keeps the row of a tool the repository owns."""
    own = "| `mine/check_mine.py` | Its own rule | Repository root |"
    head = "# tools\n\n| Path | Checks | Takes |\n| --- | --- | --- |\n"
    (target / "tools" / "README.md").write_text(head + own + "\n", encoding="utf-8")
    result = _sync(upstream, target)
    lines = (target / "tools" / "README.md").read_text(encoding="utf-8").split("\n")
    assert own in lines
    assert any(line.startswith("| `check_all.py` |") for line in lines)
    assert not any(line.startswith("| `settings.py` |") for line in lines)
    assert "tools/README.md" in result.written


def test_a_dry_run_leaves_the_readme_as_it_is(upstream, target):
    """A dry run names the README as a file it would write and writes none of it."""
    result = _sync(upstream, target, dry_run=True)
    assert "tools/README.md" in result.written
    assert (target / "tools" / "README.md").read_text(encoding="utf-8") == "own readme\n"


def test_sync_names_the_settings_the_tools_read_and_the_target_lacks(upstream, target):
    """K_OWN is all the target defines, so a setting a shared checker reads is named with SushiCore's value."""
    result = _sync(upstream, target)
    assert "K_FOLDER_CEILING" in result.missing_settings
    assert result.missing_settings["K_FOLDER_CEILING"] is not None
    assert "K_OWN" not in result.missing_settings


def test_a_setting_the_target_defines_is_not_named(upstream, target):
    """A setting the target's settings file holds is left out of the missing ones."""
    (target / "tools" / "settings.py").write_text("K_FOLDER_CEILING = 3\n", encoding="utf-8")
    assert "K_FOLDER_CEILING" not in _sync(upstream, target).missing_settings


def test_the_service_hands_what_it_read_to_the_collaborators_it_is_given(upstream, target):
    """A readme merger and a settings reporter passed in decide the README text and the report."""
    calls = []

    def merge(current, source, shared):
        calls.append((current, K_SHARED in shared))
        return "merged\n"

    result = _sync(upstream, target, merge_readme=merge, missing_settings=lambda tools, own, core: {"K_X": "1"})
    assert calls == [("own readme\n", True)]
    assert (target / "tools" / "README.md").read_text(encoding="utf-8") == "merged\n"
    assert result.missing_settings == {"K_X": "1"}


K_OLD_BODY = '"""A body only SushiSkills held."""\n'
K_OLD_FILE = "# check_all.py\n# Old - https://example.com/old\n# Copyright (c) 2021-present Old\n# Old licence.\n" + K_OLD_BODY


def _old_copy(target) -> None:
    """Writes a file the tag never held over the shared file of the target."""
    path = target / K_SHARED
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(K_OLD_FILE, encoding="utf-8")


def test_a_file_equal_to_a_pre_move_digest_is_stale_not_a_local_edit(upstream, target):
    """A body SushiSkills held before the move is replaced, whatever licence header it sits under."""
    _old_copy(target)
    known = {K_SHARED: frozenset({hashlib.sha256(K_OLD_BODY.encode("utf-8")).hexdigest()})}
    result = _sync(upstream, target, pre_move=lambda: known)
    assert K_SHARED in result.written
    assert K_OLD_BODY not in (target / K_SHARED).read_text(encoding="utf-8")


def test_a_file_matching_no_digest_and_no_release_is_still_a_local_edit(upstream, target):
    """The same file with no matching digest stops the sync."""
    _old_copy(target)
    with pytest.raises(LocalEditsError) as refused:
        _sync(upstream, target, pre_move=dict)
    assert refused.value.files == [K_SHARED]
