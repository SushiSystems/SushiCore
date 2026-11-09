# migration_fakes.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Trees and helpers the migration tests share."""

from __future__ import annotations

import dataclasses
import shutil
from collections import namedtuple
from pathlib import Path

from sushicore.provision.migration_disk import ASIDE_SUFFIX
from sushicore.provision.migration_journal import MigrationJournal
from sushicore.provision.migration_plan import plan


K_FILES = {
    "toolchains/llvm-sycl/bin/clang++.exe": b"clang",
    "vcpkg/installed/x.lib": b"library",
    "tools/cmake/bin/cmake.exe": b"cmake-binary",
}

Usage = namedtuple("Usage", "total used free")


def build_roots(tmp_path) -> tuple[Path, Path]:
    """Build the old tree with three components and a loose file, and name the new root."""
    old = tmp_path / "old"
    for name, data in K_FILES.items():
        (old / name).parent.mkdir(parents=True, exist_ok=True)
        (old / name).write_bytes(data)
    (old / ".lock").write_text("1", encoding="utf-8")
    return old, tmp_path / "new"


def snapshot(root: Path) -> dict[str, bytes]:
    """Return the bytes of every file under *root* by relative path."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def copying(old: Path, new: Path):
    """Return the plan for *old* and *new* as though they were on different volumes."""
    return dataclasses.replace(plan(old, new), same_volume=False)


def steps(new: Path) -> list[tuple[str, str]]:
    """Return the journal of *new* as ``(step, name)`` pairs."""
    return [(e["step"], e.get("name", "")) for e in MigrationJournal(new).entries()]


def interrupt_copy_of(monkeypatch, old: Path, name: str) -> None:
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


def aside(old: Path) -> Path:
    """Return the path the old root is set aside under."""
    return old.with_name(old.name + ASIDE_SUFFIX)
