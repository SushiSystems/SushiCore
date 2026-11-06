# test_importer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
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
    ImportResult,
    check_backlog,
)
from sushicore.backlog.importer import area_key

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

The step reads the old buffer; the figures are in [the report](PHYSICS/README.md#step).

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
        "docs/guides/BUILD.md": "Read reference/KNOWN_ISSUES.md first.\n",
        "modules/physics/README.md": "# Physics\n",
        "tools/run.py": "K_BACKLOG = 'docs/design/REMAINING_WORK.md'\n",
    }.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


@pytest.fixture
def imported(tmp_path: Path) -> tuple[Path, BacklogStore, ImportResult]:
    """Returns the repository after its import: the root, the store and the result."""
    root = _repository(tmp_path)
    store = BacklogStore(root, lambda: K_TODAY)
    return root, store, BacklogImporter(store).run()


@pytest.mark.small
def test_area_key_drops_small_words():
    """A section name becomes an upper case area."""
    assert area_key("Physics and matter") == "PHYSICS_MATTER"
    assert area_key("This codebase") == "CODEBASE"
    assert area_key("") == "GENERAL"


@pytest.mark.medium
def test_import_counts_the_entries_and_names_the_areas_and_pins(imported):
    """Every entry lands in a row; the areas come from the sections, the pins from `Next`."""
    _, _, result = imported
    assert (result.work, result.issues) == (3, 2)
    assert result.pins == ("RW-4",)
    assert result.areas == ("GENERAL", "PHYSICS_MATTER", "TOOLCHAINS")


@pytest.mark.medium
def test_import_writes_the_columns_of_a_work_entry(imported):
    """A state and a priority are read from the retired form, a Source from its line."""
    _, store, _ = imported
    work = store.find("RW-4").entry
    assert (work.priority, work.state) == ("P1", "open")
    assert store.find("RW-2").entry.source == "`docs/design/PHYSICS/README.md`"


@pytest.mark.medium
def test_import_writes_the_origin_of_a_sibling_issue(imported):
    """An issue of a sibling keeps its repository and ID in Origin."""
    _, store, _ = imported
    assert store.find("KI-2").entry.origin == "sushiruntime KI-4"


@pytest.mark.medium
def test_import_moves_the_prose_into_a_detail_file(imported):
    """The prose and the extra lines of an entry land in its detail file."""
    _, store, _ = imported
    detail = store.detail_path("RW-4").read_text(encoding="utf-8")
    assert "- Where: `modules/physics`" in detail and "old buffer" in detail


@pytest.mark.medium
def test_import_rebases_the_links_of_the_prose(imported):
    """A link in the prose still reaches its target from the detail folder."""
    _, store, _ = imported
    detail = store.detail_path("RW-4").read_text(encoding="utf-8")
    assert "[the report](../../design/PHYSICS/README.md#step)" in detail


@pytest.mark.medium
def test_import_deletes_the_retired_files(imported):
    """Neither retired file is left."""
    root, _, _ = imported
    assert not (root / "docs/design/REMAINING_WORK.md").exists()
    assert not (root / "docs/reference/KNOWN_ISSUES.md").exists()


@pytest.mark.medium
def test_import_rewrites_the_citations_of_the_pages(imported):
    """A page naming a retired file names the store instead."""
    root, _, _ = imported
    assert "docs/backlog/README.md and docs/backlog/README.md" in (root / "docs/README.md").read_text(encoding="utf-8")
    assert (root / "docs/guides/BUILD.md").read_text(encoding="utf-8") == "Read backlog/README.md first.\n"


@pytest.mark.medium
def test_import_leaves_a_citation_in_code_for_its_author(imported):
    """A file that is not a page keeps its citation and is reported."""
    root, _, result = imported
    assert result.left == (root / "tools" / "run.py",)
    assert "REMAINING_WORK" in (root / "tools" / "run.py").read_text(encoding="utf-8")


@pytest.mark.medium
def test_import_writes_the_ledger_with_the_counters_and_the_closed_numbers(imported):
    """The counters follow the retired files and every number below them that is gone is closed."""
    _, store, _ = imported
    ledger = store.ledger()
    assert ledger.next == {"RW": 9, "KI": 3}
    assert ledger.is_closed("RW-1") and not ledger.is_closed("RW-4")


@pytest.mark.medium
def test_import_writes_a_store_that_checks_clean(imported):
    """The imported store passes every rule."""
    _, store, _ = imported
    assert check_backlog(store) == []


@pytest.mark.medium
def test_import_runs_once(tmp_path: Path):
    """A second import is refused."""
    root = _repository(tmp_path)
    BacklogImporter(BacklogStore(root, lambda: K_TODAY)).run()
    with pytest.raises(BacklogError):
        BacklogImporter(BacklogStore(root, lambda: K_TODAY)).run()


def _git(root: Path, *arguments: str, check: bool = True) -> str:
    """Runs git in the repository and returns its output; a failure raises unless *check* is off."""
    completed = subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *arguments],
        capture_output=True, text=True, check=check,
    )
    return completed.stdout


@pytest.mark.medium
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
    _git(root, "merge", "-q", "side", check=False)
    result = BacklogRenumberer(store, "main").run()
    assert result.renames == (("RW-9", "RW-10"),)
    assert store.find("RW-9").entry.title == "Main work"
    assert store.find("RW-10").entry.title == "Side work"
    assert check_backlog(store) == []
