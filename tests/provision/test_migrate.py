# test_migrate.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the dependency-root migration, on real temporary trees with real links."""

from __future__ import annotations

import json
import os
import shutil
import stat
from pathlib import Path

import pytest

from sushicore.provision.links import is_dir_link, link_target
from sushicore.provision.migrate import (
    JOURNAL,
    JOURNAL_DONE,
    MigrationError,
    MigrationJournal,
    finalize,
    migrate,
    plan,
    rollback,
)

from .migration_fakes import Usage, aside, copying, interrupt_copy_of, snapshot, steps


@pytest.mark.medium
def test_a_same_volume_run_moves_each_component_into_the_new_root(roots):
    """Check that a same-volume run moves each component and sets the old tree aside."""
    old, new = roots
    before = snapshot(old)
    migrate(plan(old, new), lambda _line: None)
    assert snapshot(new).items() >= {k: v for k, v in before.items() if k != ".lock"}.items()
    assert snapshot(aside(old)) == {".lock": b"1"}
    assert steps(new) == [
        ("moved", "toolchains"), ("moved", "tools"), ("moved", "vcpkg"),
        ("aside", ""), ("linked", "")]


@pytest.mark.medium
def test_a_same_volume_run_links_the_old_path_to_the_new_root(roots):
    """Check that the old path becomes a link that shows the new root's files and is reported."""
    old, new = roots
    reports: list[str] = []
    migrate(plan(old, new), reports.append)
    assert is_dir_link(old)
    assert link_target(old).resolve() == new.resolve()
    assert (old / "tools/cmake/bin/cmake.exe").read_bytes() == b"cmake-binary"
    assert any("linked" in line for line in reports)


@pytest.mark.medium
def test_a_cross_volume_run_copies_each_component_and_keeps_the_old_tree_aside(roots):
    """Check that a cross-volume run copies each component and leaves no partial copy."""
    old, new = roots
    before = snapshot(old)
    migrate(copying(old, new), lambda _line: None)
    assert snapshot(aside(old)) == before
    assert [step for step, _name in steps(new)].count("copied") == 3
    assert not list(new.glob("*.partial"))


@pytest.mark.medium
def test_a_cross_volume_run_links_the_old_path_to_the_new_root(roots):
    """Check that the old path becomes a link that shows the copied files."""
    old, new = roots
    migrate(copying(old, new), lambda _line: None)
    assert is_dir_link(old)
    assert (old / "tools/cmake/bin/cmake.exe").read_bytes() == b"cmake-binary"


@pytest.mark.medium
def test_migrate_refuses_when_space_is_short(roots, monkeypatch):
    """Check that a copy is refused, with both numbers, when the target is too small."""
    old, new = roots
    monkeypatch.setattr(shutil, "disk_usage", lambda _path: Usage(100, 90, 10))
    short = copying(old, new)
    assert not short.enough_space
    with pytest.raises(MigrationError, match=r"26 bytes needed, 10 bytes free"):
        migrate(short, lambda _line: None)
    assert not new.exists()
    assert not is_dir_link(old)


@pytest.mark.medium
def test_migrate_reports_already_migrated_and_changes_nothing(roots):
    """Check that a second run reports the finished migration and leaves the journal."""
    old, new = roots
    migrate(plan(old, new), lambda _line: None)
    journal = (new / JOURNAL).read_text(encoding="utf-8")
    again = plan(old, new)
    reports: list[str] = []
    migrate(again, reports.append)
    assert again.already_migrated
    assert again.moves == ()
    assert reports[0].startswith("already migrated")
    assert (new / JOURNAL).read_text(encoding="utf-8") == journal


@pytest.mark.medium
def test_interrupted_copy_resumes_and_finishes_the_migration(roots, monkeypatch):
    """Check that a re-run after an interrupt finishes the copy and leaves no partial."""
    old, new = roots
    before = snapshot(old)
    interrupt_copy_of(monkeypatch, old, "vcpkg")
    with pytest.raises(KeyboardInterrupt):
        migrate(copying(old, new), lambda _line: None)
    assert (new / "vcpkg.partial").is_dir()
    migrate(copying(old, new), lambda _line: None)
    assert snapshot(aside(old)) == before
    assert not (new / "vcpkg.partial").exists()


@pytest.mark.medium
def test_a_resumed_copy_records_each_finished_component_once(roots, monkeypatch):
    """Check that the journal holds one copied step per component after an interrupted run."""
    old, new = roots
    interrupt_copy_of(monkeypatch, old, "vcpkg")
    with pytest.raises(KeyboardInterrupt):
        migrate(copying(old, new), lambda _line: None)
    migrate(copying(old, new), lambda _line: None)
    assert sorted(name for step, name in steps(new) if step == "copied") == [
        "toolchains", "tools", "vcpkg"]


@pytest.mark.medium
def test_rollback_after_a_refused_rename_restores_the_original_tree(roots, monkeypatch):
    """Check that the components moved before a refused rename go back."""
    old, new = roots
    before = snapshot(old)
    real_rename = os.rename

    def rename(source, target):
        """Refuse to move vcpkg into the new root."""
        if Path(source).name == "vcpkg" and Path(target).parent == new:
            raise PermissionError(13, "in use", str(source))
        real_rename(source, target)

    monkeypatch.setattr(os, "rename", rename)
    with pytest.raises(MigrationError):
        migrate(plan(old, new), lambda _line: None)
    rollback(old, new, lambda _line: None)
    assert snapshot(old) == before
    assert not (new / JOURNAL).exists()


@pytest.mark.medium
def test_interrupted_rename_run_resumes_from_the_journal(roots, monkeypatch):
    """Check that a same-volume run stopped part-way finishes on the next run."""
    old, new = roots
    real_rename = os.rename
    refuse = {"vcpkg"}

    def rename(source, target):
        """Refuse vcpkg the first time only."""
        if Path(source).name in refuse:
            refuse.clear()
            raise PermissionError(13, "in use", str(source))
        real_rename(source, target)

    monkeypatch.setattr(os, "rename", rename)
    with pytest.raises(MigrationError):
        migrate(plan(old, new), lambda _line: None)
    again = plan(old, new)
    assert [m.name for m in again.moves] == ["vcpkg"]
    migrate(again, lambda _line: None)
    assert is_dir_link(old)
    assert (old / "vcpkg/installed/x.lib").read_bytes() == b"library"


@pytest.mark.medium
def test_rollback_after_success_restores_the_original_tree(roots):
    """Check that a rollback of a same-volume run leaves the old tree as it was."""
    old, new = roots
    before = snapshot(old)
    migrate(plan(old, new), lambda _line: None)
    rollback(old, new, lambda _line: None)
    assert old.is_dir() and not is_dir_link(old)
    assert snapshot(old) == before
    assert not aside(old).exists()
    assert sorted(p.name for p in new.iterdir()) == [".lock"]


@pytest.mark.medium
def test_rollback_after_a_copy_restores_the_original_tree(roots):
    """Check that a rollback of a cross-volume run deletes the copies and the link."""
    old, new = roots
    before = snapshot(old)
    migrate(copying(old, new), lambda _line: None)
    rollback(old, new, lambda _line: None)
    assert old.is_dir() and not is_dir_link(old)
    assert snapshot(old) == before
    assert sorted(p.name for p in new.iterdir()) == [".lock"]


@pytest.mark.medium
def test_rollback_after_an_interrupted_copy_restores_the_original_tree(roots, monkeypatch):
    """Check that a rollback after an interrupt removes the copies and the partial one."""
    old, new = roots
    before = snapshot(old)
    real_copytree = shutil.copytree

    def copytree(source, target, *args, **kwargs):
        """Stop at vcpkg, leaving a partial copy behind."""
        if Path(source).name == "vcpkg":
            Path(target).mkdir()
            raise KeyboardInterrupt
        return real_copytree(source, target, *args, **kwargs)

    monkeypatch.setattr(shutil, "copytree", copytree)
    with pytest.raises(KeyboardInterrupt):
        migrate(copying(old, new), lambda _line: None)
    rollback(old, new, lambda _line: None)
    assert snapshot(old) == before
    assert sorted(p.name for p in new.iterdir()) == [".lock"]


@pytest.mark.medium
def test_rollback_never_deletes_the_only_copy(roots):
    """Check that a copy is kept when the old root no longer holds its original."""
    old, new = roots
    migrate(copying(old, new), lambda _line: None)
    shutil.rmtree(aside(old) / "vcpkg")
    with pytest.raises(MigrationError, match="only copy"):
        rollback(old, new, lambda _line: None)
    assert (new / "vcpkg/installed/x.lib").is_file()
    assert (new / JOURNAL).is_file()


@pytest.mark.medium
def test_rollback_without_a_journal_reports_nothing_to_do(roots):
    """Check that a rollback with no journal reports it and changes nothing."""
    old, new = roots
    reports: list[str] = []
    rollback(old, new, reports.append)
    assert reports == ["nothing to roll back"]
    assert not new.exists()


@pytest.mark.medium
def test_rollback_skips_the_steps_another_program_recorded(roots):
    """Check that a journal step this module does not know is left alone."""
    old, new = roots
    before = snapshot(old)
    migrate(plan(old, new), lambda _line: None)
    MigrationJournal(new).append("environment", name="SUSHISYSTEMS_HOME", previous=None)
    rollback(old, new, lambda _line: None)
    assert snapshot(old) == before


@pytest.mark.medium
def test_finalize_deletes_the_aside_copy_and_keeps_the_link(roots):
    """Check that finalize deletes the aside copy, a read-only file included."""
    old, new = roots
    migrate(copying(old, new), lambda _line: None)
    os.chmod(aside(old) / "vcpkg/installed/x.lib", stat.S_IREAD)
    finalize(old, new, lambda _line: None)
    assert not aside(old).exists()
    assert is_dir_link(old)


@pytest.mark.medium
def test_finalize_closes_the_journal_with_a_finalized_step(roots):
    """Check that finalize renames the journal and ends it with a finalized step."""
    old, new = roots
    migrate(copying(old, new), lambda _line: None)
    finalize(old, new, lambda _line: None)
    last = json.loads((new / JOURNAL_DONE).read_text(encoding="utf-8").splitlines()[-1])
    assert (new / JOURNAL_DONE).is_file()
    assert last == {"step": "finalized"}


@pytest.mark.medium
def test_a_rollback_after_finalize_has_nothing_to_do(roots):
    """Check that a rollback after finalize reports that there is nothing to roll back."""
    old, new = roots
    migrate(copying(old, new), lambda _line: None)
    finalize(old, new, lambda _line: None)
    reports: list[str] = []
    rollback(old, new, reports.append)
    assert reports == ["nothing to roll back"]
    assert (old / "vcpkg/installed/x.lib").read_bytes() == b"library"


@pytest.mark.medium
def test_finalize_refuses_before_migration_and_deletes_nothing(roots):
    """Check that finalize refuses an old root that is not a link."""
    old, new = roots
    before = snapshot(old)
    with pytest.raises(MigrationError, match="not a link"):
        finalize(old, new, lambda _line: None)
    assert snapshot(old) == before


@pytest.mark.medium
def test_finalize_refuses_a_second_time(roots):
    """Check that finalize refuses when the aside copy is already gone."""
    old, new = roots
    migrate(plan(old, new), lambda _line: None)
    finalize(old, new, lambda _line: None)
    with pytest.raises(MigrationError, match="does not exist"):
        finalize(old, new, lambda _line: None)
    assert is_dir_link(old)


@pytest.mark.medium
def test_finalize_with_drop_link_removes_the_link_and_the_aside_copy(roots):
    """Check that drop_link removes the link at the old path along with the aside copy."""
    old, new = roots
    migrate(plan(old, new), lambda _line: None)
    finalize(old, new, lambda _line: None, drop_link=True)
    assert not old.exists() and not is_dir_link(old)
    assert not aside(old).exists()


@pytest.mark.medium
def test_finalize_with_drop_link_keeps_the_new_root(roots):
    """Check that drop_link deletes nothing under the new root."""
    old, new = roots
    migrate(plan(old, new), lambda _line: None)
    finalize(old, new, lambda _line: None, drop_link=True)
    assert (new / "vcpkg/installed/x.lib").read_bytes() == b"library"


@pytest.mark.medium
def test_finalize_can_drop_the_link_after_an_earlier_finalize(roots):
    """Check that drop_link still works once the aside copy is gone."""
    old, new = roots
    migrate(plan(old, new), lambda _line: None)
    finalize(old, new, lambda _line: None)
    finalize(old, new, lambda _line: None, drop_link=True)
    assert not is_dir_link(old)
    assert (new / "tools/cmake/bin/cmake.exe").is_file()
