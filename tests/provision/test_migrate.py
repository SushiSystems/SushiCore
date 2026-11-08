# test_migrate.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the dependency-root migration, on real temporary trees with real links."""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import stat
from collections import namedtuple
from pathlib import Path

import pytest

from sushicore.provision.links import is_dir_link, link_target, make_dir_link
from sushicore.provision.migrate import (
    ASIDE_SUFFIX,
    JOURNAL,
    JOURNAL_DONE,
    MigrationError,
    MigrationJournal,
    PlanProbes,
    finalize,
    migrate,
    plan,
    rollback,
)


_FILES = {
    "toolchains/llvm-sycl/bin/clang++.exe": b"clang",
    "vcpkg/installed/x.lib": b"library",
    "tools/cmake/bin/cmake.exe": b"cmake-binary",
}

_Usage = namedtuple("_Usage", "total used free")


@pytest.fixture
def roots(tmp_path) -> tuple[Path, Path]:
    """Build the old tree with three components and a loose file, and name the new root."""
    old = tmp_path / "old"
    for name, data in _FILES.items():
        (old / name).parent.mkdir(parents=True, exist_ok=True)
        (old / name).write_bytes(data)
    (old / ".lock").write_text("1", encoding="utf-8")
    return old, tmp_path / "new"


def _snapshot(root: Path) -> dict[str, bytes]:
    """Return the bytes of every file under *root* by relative path."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def _copying(old: Path, new: Path):
    """Return the plan for *old* and *new* as though they were on different volumes."""
    return dataclasses.replace(plan(old, new), same_volume=False)


def _steps(new: Path) -> list[tuple[str, str]]:
    """Return the journal of *new* as ``(step, name)`` pairs."""
    return [(e["step"], e.get("name", "")) for e in MigrationJournal(new).entries()]


def _interrupt_copy_of(monkeypatch, old: Path, name: str) -> None:
    """Make the first copy of the component *name* under *old* stop, leaving a partial copy."""
    real_copytree = shutil.copytree
    pending = {name}

    def copytree(source, target, *args, **kwargs):
        """Stop at the named component the first time."""
        if Path(source).parent == old and Path(source).name in pending:
            pending.clear()
            Path(target).mkdir()
            raise KeyboardInterrupt
        return real_copytree(source, target, *args, **kwargs)

    monkeypatch.setattr(shutil, "copytree", copytree)


def _aside(old: Path) -> Path:
    """Return the path the old root is set aside under."""
    return old.with_name(old.name + ASIDE_SUFFIX)


K_OLD = Path("/machine/old")
K_NEW = Path("/machine/new")

#: What the old root holds: each component with the size of its single file.
K_COMPONENTS = {"toolchains": 5, "tools": 12, "vcpkg": 7}


def _probes(**overrides) -> PlanProbes:
    """Return probes for an old root holding the three components, a free new root, one volume."""
    values = dict(
        is_link=lambda path: False,
        link_target=lambda path: None,
        is_dir=lambda path: path == K_OLD,
        present=lambda path: False,
        resolve=lambda path: path,
        subfolders=lambda path: [K_OLD / name for name in K_COMPONENTS],
        file_sizes=lambda path: {"file": K_COMPONENTS[path.name]},
        free_bytes=lambda path: 1000,
        same_volume=lambda old, new: True,
        journal_exists=lambda root: False)
    values.update(overrides)
    return PlanProbes(**values)


@pytest.mark.small
def test_plan_counts_files_and_bytes_per_component():
    """Check that plan counts the files and bytes of each top-level directory."""
    found = plan(K_OLD, K_NEW, _probes())
    assert [(m.name, m.files, m.bytes) for m in found.moves] == [
        ("toolchains", 1, 5), ("tools", 1, 12), ("vcpkg", 1, 7)]
    assert (found.total_bytes, found.moves[0].target) == (24, K_NEW / "toolchains")


@pytest.mark.small
def test_plan_reports_one_volume_for_two_folders_side_by_side():
    """Check that two roots on one volume need no space."""
    found = plan(K_OLD, K_NEW, _probes(free_bytes=lambda path: 0))
    assert found.same_volume
    assert found.enough_space


@pytest.mark.small
def test_plan_reports_a_short_target_volume_when_the_volumes_differ():
    """Check that a copy to another volume with too little space is not enough."""
    found = plan(K_OLD, K_NEW, _probes(same_volume=lambda old, new: False,
                                       free_bytes=lambda path: 10))
    assert not found.enough_space


@pytest.mark.small
def test_plan_rejects_a_name_already_in_the_target():
    """Check that plan refuses when the target holds a component's name."""
    probes = _probes(present=lambda path: path == K_NEW / "vcpkg")
    with pytest.raises(MigrationError, match="vcpkg"):
        plan(K_OLD, K_NEW, probes)


@pytest.mark.small
def test_plan_ignores_lock_and_registry_in_the_target():
    """Check that the lock and the registry of the target are not collisions."""
    probes = _probes(present=lambda path: path.name in (".lock", "registry.toml"))
    assert len(plan(K_OLD, K_NEW, probes).moves) == 3


@pytest.mark.small
def test_plan_rejects_a_target_inside_the_old_root():
    """Check that plan refuses a new root that lies under the old one."""
    with pytest.raises(MigrationError, match="inside"):
        plan(K_OLD, K_OLD / "moved", _probes())


@pytest.mark.small
def test_plan_rejects_a_missing_old_root():
    """Check that plan refuses an old root that does not exist."""
    with pytest.raises(MigrationError, match="not a directory"):
        plan(K_OLD, K_NEW, _probes(is_dir=lambda path: False))


@pytest.mark.small
def test_plan_rejects_an_old_root_linked_elsewhere():
    """Check that plan refuses an old root that links to another directory."""
    other = Path("/machine/other")
    probes = _probes(is_link=lambda path: path == K_OLD,
                     link_target=lambda path: other if path == K_OLD else None)
    with pytest.raises(MigrationError, match="is a link"):
        plan(K_OLD, K_NEW, probes)


@pytest.mark.medium
def test_a_same_volume_run_moves_each_component_into_the_new_root(roots):
    """Check that a same-volume run moves each component and sets the old tree aside."""
    old, new = roots
    before = _snapshot(old)
    migrate(plan(old, new), lambda _line: None)
    assert _snapshot(new).items() >= {k: v for k, v in before.items() if k != ".lock"}.items()
    assert _snapshot(_aside(old)) == {".lock": b"1"}
    assert _steps(new) == [
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
    before = _snapshot(old)
    migrate(_copying(old, new), lambda _line: None)
    assert _snapshot(_aside(old)) == before
    assert [step for step, _name in _steps(new)].count("copied") == 3
    assert not list(new.glob("*.partial"))


@pytest.mark.medium
def test_a_cross_volume_run_links_the_old_path_to_the_new_root(roots):
    """Check that the old path becomes a link that shows the copied files."""
    old, new = roots
    migrate(_copying(old, new), lambda _line: None)
    assert is_dir_link(old)
    assert (old / "tools/cmake/bin/cmake.exe").read_bytes() == b"cmake-binary"


@pytest.mark.medium
def test_migrate_refuses_when_space_is_short(roots, monkeypatch):
    """Check that a copy is refused, with both numbers, when the target is too small."""
    old, new = roots
    monkeypatch.setattr(shutil, "disk_usage", lambda _path: _Usage(100, 90, 10))
    short = _copying(old, new)
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
    before = _snapshot(old)
    _interrupt_copy_of(monkeypatch, old, "vcpkg")
    with pytest.raises(KeyboardInterrupt):
        migrate(_copying(old, new), lambda _line: None)
    assert (new / "vcpkg.partial").is_dir()
    migrate(_copying(old, new), lambda _line: None)
    assert _snapshot(_aside(old)) == before
    assert not (new / "vcpkg.partial").exists()


@pytest.mark.medium
def test_a_resumed_copy_records_each_finished_component_once(roots, monkeypatch):
    """Check that the journal holds one copied step per component after an interrupted run."""
    old, new = roots
    _interrupt_copy_of(monkeypatch, old, "vcpkg")
    with pytest.raises(KeyboardInterrupt):
        migrate(_copying(old, new), lambda _line: None)
    migrate(_copying(old, new), lambda _line: None)
    assert sorted(name for step, name in _steps(new) if step == "copied") == [
        "toolchains", "tools", "vcpkg"]


@pytest.mark.medium
def test_verify_failure_stops_before_the_swap_and_leaves_old_untouched(roots):
    """Check that a copy that differs stops the run with the old tree as it was."""
    old, new = roots
    before = _snapshot(old)
    with pytest.raises(MigrationError, match="toolchains"):
        migrate(_copying(old, new), lambda _line: None, verify=lambda _source, _copy: False)
    assert not is_dir_link(old)
    assert _snapshot(old) == before
    assert not _aside(old).exists()
    assert not (new / "toolchains").exists()


@pytest.mark.medium
def test_copy_with_a_missing_file_fails_verification(roots, monkeypatch):
    """Check that a copy that lost a file is told apart from its source."""
    old, new = roots
    real_copytree = shutil.copytree

    def lossy(source, target, *args, **kwargs):
        """Copy the tree and then delete one file of the copy."""
        real_copytree(source, target, *args, **kwargs)
        for path in Path(target).rglob("*.exe"):
            path.unlink()

    monkeypatch.setattr(shutil, "copytree", lossy)
    with pytest.raises(MigrationError, match="differs"):
        migrate(_copying(old, new), lambda _line: None)
    assert not is_dir_link(old)


@pytest.mark.medium
def test_unreadable_file_stops_the_copy_before_the_swap(roots, monkeypatch):
    """Check that a file the copy cannot read stops the run and leaves no partial copy."""
    old, new = roots

    def failing(source, target, *args, **kwargs):
        """Stand in for a copy that meets a locked file."""
        Path(target).mkdir()
        raise shutil.Error([(str(source), str(target), "locked")])

    monkeypatch.setattr(shutil, "copytree", failing)
    with pytest.raises(MigrationError, match="could not be copied"):
        migrate(_copying(old, new), lambda _line: None)
    assert not is_dir_link(old)
    assert not list(new.glob("*.partial"))


@pytest.mark.medium
def test_rename_of_a_component_in_use_names_it_and_keeps_the_journal(roots, monkeypatch):
    """Check that a rename refused for an open file names the component and the cause."""
    old, new = roots
    real_rename = os.rename

    def rename(source, target):
        """Refuse to move vcpkg, as Windows does while a file in it is open."""
        if Path(source).name == "vcpkg":
            raise PermissionError(13, "The process cannot access the file", str(source))
        real_rename(source, target)

    monkeypatch.setattr(os, "rename", rename)
    with pytest.raises(MigrationError, match="vcpkg: a process still uses"):
        migrate(plan(old, new), lambda _line: None)
    assert _steps(new) == [("moved", "toolchains"), ("moved", "tools")]
    assert not is_dir_link(old)
    assert (old / "vcpkg/installed/x.lib").is_file()


@pytest.mark.medium
def test_rollback_after_a_refused_rename_restores_the_original_tree(roots, monkeypatch):
    """Check that the components moved before a refused rename go back."""
    old, new = roots
    before = _snapshot(old)
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
    assert _snapshot(old) == before
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
    before = _snapshot(old)
    migrate(plan(old, new), lambda _line: None)
    rollback(old, new, lambda _line: None)
    assert old.is_dir() and not is_dir_link(old)
    assert _snapshot(old) == before
    assert not _aside(old).exists()
    assert sorted(p.name for p in new.iterdir()) == [".lock"]


@pytest.mark.medium
def test_rollback_after_a_copy_restores_the_original_tree(roots):
    """Check that a rollback of a cross-volume run deletes the copies and the link."""
    old, new = roots
    before = _snapshot(old)
    migrate(_copying(old, new), lambda _line: None)
    rollback(old, new, lambda _line: None)
    assert old.is_dir() and not is_dir_link(old)
    assert _snapshot(old) == before
    assert sorted(p.name for p in new.iterdir()) == [".lock"]


@pytest.mark.medium
def test_rollback_after_an_interrupted_copy_restores_the_original_tree(roots, monkeypatch):
    """Check that a rollback after an interrupt removes the copies and the partial one."""
    old, new = roots
    before = _snapshot(old)
    real_copytree = shutil.copytree

    def copytree(source, target, *args, **kwargs):
        """Stop at vcpkg, leaving a partial copy behind."""
        if Path(source).name == "vcpkg":
            Path(target).mkdir()
            raise KeyboardInterrupt
        return real_copytree(source, target, *args, **kwargs)

    monkeypatch.setattr(shutil, "copytree", copytree)
    with pytest.raises(KeyboardInterrupt):
        migrate(_copying(old, new), lambda _line: None)
    rollback(old, new, lambda _line: None)
    assert _snapshot(old) == before
    assert sorted(p.name for p in new.iterdir()) == [".lock"]


@pytest.mark.medium
def test_rollback_never_deletes_the_only_copy(roots):
    """Check that a copy is kept when the old root no longer holds its original."""
    old, new = roots
    migrate(_copying(old, new), lambda _line: None)
    shutil.rmtree(_aside(old) / "vcpkg")
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
    before = _snapshot(old)
    migrate(plan(old, new), lambda _line: None)
    MigrationJournal(new).append("environment", name="SUSHISYSTEMS_HOME", previous=None)
    rollback(old, new, lambda _line: None)
    assert _snapshot(old) == before


@pytest.mark.medium
def test_finalize_deletes_the_aside_copy_and_keeps_the_link(roots):
    """Check that finalize deletes the aside copy, a read-only file included."""
    old, new = roots
    migrate(_copying(old, new), lambda _line: None)
    os.chmod(_aside(old) / "vcpkg/installed/x.lib", stat.S_IREAD)
    finalize(old, new, lambda _line: None)
    assert not _aside(old).exists()
    assert is_dir_link(old)


@pytest.mark.medium
def test_finalize_closes_the_journal_with_a_finalized_step(roots):
    """Check that finalize renames the journal and ends it with a finalized step."""
    old, new = roots
    migrate(_copying(old, new), lambda _line: None)
    finalize(old, new, lambda _line: None)
    last = json.loads((new / JOURNAL_DONE).read_text(encoding="utf-8").splitlines()[-1])
    assert (new / JOURNAL_DONE).is_file()
    assert last == {"step": "finalized"}


@pytest.mark.medium
def test_a_rollback_after_finalize_has_nothing_to_do(roots):
    """Check that a rollback after finalize reports that there is nothing to roll back."""
    old, new = roots
    migrate(_copying(old, new), lambda _line: None)
    finalize(old, new, lambda _line: None)
    reports: list[str] = []
    rollback(old, new, reports.append)
    assert reports == ["nothing to roll back"]
    assert (old / "vcpkg/installed/x.lib").read_bytes() == b"library"


@pytest.mark.medium
def test_finalize_refuses_before_migration_and_deletes_nothing(roots):
    """Check that finalize refuses an old root that is not a link."""
    old, new = roots
    before = _snapshot(old)
    with pytest.raises(MigrationError, match="not a link"):
        finalize(old, new, lambda _line: None)
    assert _snapshot(old) == before


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
    assert not _aside(old).exists()


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


@pytest.mark.medium
def test_copy_recreates_a_link_inside_a_component(roots):
    """Check that a directory link inside a component is copied as a link and counted once."""
    old, new = roots
    make_dir_link(old / "vcpkg" / "current", old / "vcpkg" / "installed")
    found = _copying(old, new)
    assert next(m for m in found.moves if m.name == "vcpkg").files == 2
    migrate(found, lambda _line: None)
    assert is_dir_link(new / "vcpkg" / "current")
    assert (new / "vcpkg" / "current" / "x.lib").read_bytes() == b"library"


@pytest.mark.medium
def test_journal_leaves_out_a_line_cut_short(tmp_path):
    """Check that a journal line that is not whole JSON is not returned."""
    journal = MigrationJournal(tmp_path)
    journal.append("moved", name="tools")
    with (tmp_path / JOURNAL).open("a", encoding="utf-8") as stream:
        stream.write('{"step": "mov')
    assert journal.entries() == [{"step": "moved", "name": "tools"}]
    assert journal.names("moved") == {"tools"}
