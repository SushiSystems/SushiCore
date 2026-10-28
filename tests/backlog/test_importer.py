# test_importer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests `import` from the retired files and `renumber` across two branches."""

from __future__ import annotations

import datetime
import subprocess
from pathlib import Path

import pytest

from sushicore.backlog import (
    BacklogError,
    BacklogImporter,
    BacklogRenumberer,
    BacklogStore,
    check_backlog,
)
from sushicore.backlog.importer import area_key

pytestmark = pytest.mark.medium

K_TODAY = datetime.date(2026, 10, 28)
K_WORK = """# Remaining work

Next id: RW-9

## Next

- RW-4 The step comes first

## Decisions waiting for the owner

### RW-2 Choose the solver
- State: decision
- Done when: the owner has chosen one
- Source: `docs/design/PHYSICS/README.md`

## Physics and matter

### RW-4 Fix the step
- State: open
- Done when: the step test passes
- Where: `modules/physics`

The step reads the old buffer; the figures are in the report.

### RW-5 Bind the late operand
- State: blocked
- Blocked by: RW-4
- Done when: the recorder accepts it
"""
K_ISSUES = """# Known issues

Next id: KI-3

## Toolchains

### KI-1 The link fails on a second run
- Origin: toolchain
- Cause: unknown
- Recognise: the second link prints a permission error
- Workaround: link once

### KI-2 The host faults reading shared memory
- Origin: sushiruntime
- Upstream: sushiruntime KI-4
- Recognise: an access fault in a print
- Workaround: none
"""


def _repository(tmp_path: Path) -> Path:
    """Writes a repository with the two retired files and a page that cites them."""
    root = tmp_path / "repo"
    for relative, text in {
        "docs/design/REMAINING_WORK.md": K_WORK,
        "docs/reference/KNOWN_ISSUES.md": K_ISSUES,
        "docs/design/PHYSICS/README.md": "# Physics\n",
        "docs/README.md": "See docs/design/REMAINING_WORK.md and docs/reference/KNOWN_ISSUES.md.\n",
        "modules/physics/README.md": "# Physics\n",
        "tools/run.py": "K_BACKLOG = 'docs/design/REMAINING_WORK.md'\n",
    }.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def test_area_key_drops_small_words():
    """A section name becomes an upper case area."""
    assert area_key("Physics and matter") == "PHYSICS_MATTER"
    assert area_key("This codebase") == "CODEBASE"
    assert area_key("") == "GENERAL"


def test_import_writes_a_clean_store_and_deletes_the_retired_files(tmp_path: Path):
    """Every entry lands in a row, the prose in a detail file, and the citations move."""
    root = _repository(tmp_path)
    store = BacklogStore(root, lambda: K_TODAY)
    result = BacklogImporter(store).run()
    assert (result.work, result.issues) == (3, 2)
    assert result.pins == ("RW-4",)
    assert result.areas == ("GENERAL", "PHYSICS_MATTER", "TOOLCHAINS")
    assert not (root / "docs/design/REMAINING_WORK.md").exists()
    assert result.left == (root / "tools" / "run.py",)
    assert "REMAINING_WORK" in (root / "tools" / "run.py").read_text(encoding="utf-8")
    assert "docs/backlog/README.md and docs/backlog/README.md" in (root / "docs/README.md").read_text(encoding="utf-8")
    work = store.find("RW-4").entry
    assert (work.priority, work.state) == ("P1", "open")
    detail = store.detail_path("RW-4").read_text(encoding="utf-8")
    assert "- Where: `modules/physics`" in detail and "old buffer" in detail
    assert store.find("RW-2").entry.source == "`docs/design/PHYSICS/README.md`"
    assert store.find("KI-2").entry.origin == "sushiruntime KI-4"
    ledger = store.ledger()
    assert ledger.next == {"RW": 9, "KI": 3}
    assert ledger.is_closed("RW-1") and not ledger.is_closed("RW-4")
    assert check_backlog(store) == []


def test_import_runs_once(tmp_path: Path):
    """A second import is refused."""
    root = _repository(tmp_path)
    BacklogImporter(BacklogStore(root, lambda: K_TODAY)).run()
    with pytest.raises(BacklogError):
        BacklogImporter(BacklogStore(root, lambda: K_TODAY)).run()


def _git(root: Path, *arguments: str) -> str:
    """Runs git in the repository and returns its output."""
    completed = subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *arguments],
        capture_output=True, text=True, check=False,
    )
    return completed.stdout


def test_renumber_keeps_the_target_branch_entry_and_moves_the_other(tmp_path: Path):
    """Two branches that each took RW-9: main keeps it, the side's entry becomes RW-10."""
    from sushicore.backlog import BacklogEditor

    root = _repository(tmp_path)
    store = BacklogStore(root, lambda: K_TODAY)
    BacklogImporter(store).run()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "start")
    _git(root, "checkout", "-q", "-b", "side")
    BacklogEditor(store).add_work(area="PHYSICS_MATTER", priority="P2", title="Side work", done_when="side done")
    _git(root, "commit", "-q", "-am", "side")
    _git(root, "checkout", "-q", "main")
    BacklogEditor(store).add_work(area="PHYSICS_MATTER", priority="P2", title="Main work", done_when="main done")
    _git(root, "commit", "-q", "-am", "main")
    _git(root, "merge", "-q", "side")
    result = BacklogRenumberer(store, "main").run()
    assert result.renames == (("RW-9", "RW-10"),)
    assert store.find("RW-9").entry.title == "Main work"
    assert store.find("RW-10").entry.title == "Side work"
    assert check_backlog(store) == []
