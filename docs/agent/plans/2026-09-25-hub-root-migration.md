# Hub root migration (sub-project 2, phase B) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move hub's dependency tree from `D:\Projects\sushistack\dependencies` to `C:\Users\sushi\.sushisystems`, leave a junction at the old path so every existing absolute path keeps resolving, and make `hub migrate --rollback` undo it instantly.

**Architecture:** `sushicore.provision.links` creates, inspects and removes directory links: a junction on Windows, a symlink elsewhere. `sushicore.provision.migrate` plans the move and copies each top-level component with a journal, verifying every file by size and count. It then swaps the old folder aside (a same-volume rename) and puts a junction in its place. The old copy stays as `dependencies.pre-migrate` until the owner runs `--finalize`, so a rollback is two renames and no copying. `hub migrate` is the command. After a migration, `hub`'s `deps_dir()` returns the provision root, so new installs land there directly.

**Tech Stack:** Python 3.10+, Typer, pytest, `_winapi.CreateJunction` (CPython, Windows), `os.symlink` (Linux).

**Spec:** `D:/Projects/sushicore/docs/agent/specs/2026-09-23-provision-design.md` ("The dependency root", "Migration → Phase B").

## Global Constraints

- New root: `C:\Users\sushi\.sushisystems`, which is `home.default_root()`. No `SUSHISYSTEMS_HOME` is set (owner decision, 2026-09-25).
- The layout is unchanged. `toolchains/`, `tools/`, `vcpkg/`, `ur/` and `build/` move as they are. The versioned layout is a later step (owner decision, 2026-09-25).
- The move crosses volumes (D: → C:), so each component is copied, verified, and only then counted as moved. Nothing under the old tree is deleted before `--finalize`.
- Before any copy, free space on the target volume must be at least the tree size plus 10 %. Otherwise `migrate` refuses and names both numbers. Measured 2026-09-25: the tree is about 20 GB and C: has 38 GB free.
- Every step goes to a journal at `<new root>/.migrate-journal.jsonl`. `--rollback` replays it in reverse.
- The old path becomes a junction to the new root, so every `CMakeCache.txt`, `compile_commands.json`, `workspace.toml` and `config.local.toml` naming it still resolves. None of those files is rewritten in this plan (spec phase B step 6 is later).
- `migrate` holds `ProvisionLock` at `<new root>/.lock`. It refuses to start if the target already holds a component with the same top-level name. The existing `.lock` in the target is not a component.
- The owner is told before the real run and pauses SushiEngine work first. The real run is the owner's action (Task 5), never a subagent's.
- Every CLI runs live from these working trees. Every edit must leave files parseable at every moment. No subagent runs `se`, `sr`, `sa`, `sb` builds, cmake, ninja or ctest.
- Python files carry the Apache header and a module docstring. Every function has a Google-style docstring whose summary is one sentence starting with a verb. Changelog lines are one sentence of at most 240 characters, with no reason.

## Review Focus

1. The run is interrupted halfway through copying `vcpkg` (Ctrl+C or a crash). Re-running resumes from the journal without copying finished components again, and `--rollback` still restores the original state. (Task 2 test.)
2. The old path is already a junction, meaning the migration already happened. `migrate` reports "already migrated" and exits 0 without touching anything. (Task 2 test.)
3. A file inside the old tree is locked or unreadable during the copy. Verification fails for that component, the migration stops before the swap, and the old tree stays untouched. (Task 2 test.)
4. `--finalize` runs before a successful migration, or twice. It refuses, and deletes nothing. (Task 2 test.)
5. `hub doctor` and `hub install --dry-run` after the migration show the same components as before, now under the new root. (Task 4 test plus the owner's run.)

---

## Waves

| Wave | Tasks | Files | Waits on | Controller build after |
| --- | --- | --- | --- | --- |
| 1 | Task 1 ∥ Task 3 | sushicore `provision/links.py` ∥ `provision/registry.py` | — | sushicore pytest, hub pytest |
| 2 | Task 2 | sushicore `provision/migrate.py` | Task 1 | sushicore pytest, hub pytest |
| 3 | Task 4 | sushistack `cli/sushihub/commands` + `config.py` | Tasks 2, 3 | hub pytest, `hub migrate --dry-run`, `hub doctor` |
| 4 | Task 5 (owner) | the real move | Wave 3 | — |
| 5 | Task 6 (controller) | verification only | Task 5 | every module's doctor and build |

---

### Task 1: Directory links

**Files:**
- Create: `D:/Projects/sushicore/sushicore/provision/links.py`
- Test: `D:/Projects/sushicore/tests/provision/test_links.py`

**Interfaces:**
- Produces:
  - `make_dir_link(link: Path, target: Path) -> None`. Raises `FileExistsError` when `link` exists.
  - `is_dir_link(path: Path) -> bool`. True for a junction or a directory symlink.
  - `link_target(path: Path) -> Path | None`
  - `remove_dir_link(path: Path) -> None`. Removes only the link, never the target's contents, and raises `ValueError` when `path` is not a link.

- [ ] **Step 1: Failing tests**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for directory links."""

from __future__ import annotations

import pytest

from sushicore.provision.links import is_dir_link, link_target, make_dir_link, remove_dir_link


def test_link_resolves_to_target_contents(tmp_path):
    target = tmp_path / "new"
    (target / "tools").mkdir(parents=True)
    link = tmp_path / "old"
    make_dir_link(link, target)
    assert is_dir_link(link)
    assert (link / "tools").is_dir()
    assert link_target(link).resolve() == target.resolve()


def test_remove_keeps_target_contents(tmp_path):
    target = tmp_path / "new"
    (target / "keep.txt").parent.mkdir(parents=True)
    (target / "keep.txt").write_text("x")
    link = tmp_path / "old"
    make_dir_link(link, target)
    remove_dir_link(link)
    assert not link.exists()
    assert (target / "keep.txt").read_text() == "x"


def test_remove_refuses_a_real_directory(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    with pytest.raises(ValueError):
        remove_dir_link(real)
    assert real.is_dir()


def test_make_refuses_an_existing_path(tmp_path):
    (tmp_path / "old").mkdir()
    with pytest.raises(FileExistsError):
        make_dir_link(tmp_path / "old", tmp_path)


def test_plain_directory_is_not_a_link(tmp_path):
    assert not is_dir_link(tmp_path)
    assert link_target(tmp_path) is None
```

- [ ] **Step 2: Run** `cd D:/Projects/sushicore && python -m pytest tests/provision/test_links.py -q`. Expected: FAIL (module missing).

- [ ] **Step 3: Implement**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Creates, inspects and removes directory links: junctions on Windows, symlinks elsewhere."""

from __future__ import annotations

import os
from pathlib import Path

_IS_WINDOWS = os.name == "nt"


def make_dir_link(link: Path, target: Path) -> None:
    """Create *link* as a directory link to *target*.

    Raises:
        FileExistsError: *link* already exists.
    """
    if link.exists() or is_dir_link(link):
        raise FileExistsError(str(link))
    if _IS_WINDOWS:
        import _winapi
        _winapi.CreateJunction(str(target.resolve()), str(link))
    else:
        os.symlink(target.resolve(), link, target_is_directory=True)


def is_dir_link(path: Path) -> bool:
    """Report whether *path* is a junction or a directory symlink."""
    if path.is_symlink():
        return True
    return _IS_WINDOWS and hasattr(path, "is_junction") and path.is_junction()


def link_target(path: Path) -> Path | None:
    """Return the directory *path* links to, or None when it is not a link."""
    if not is_dir_link(path):
        return None
    return Path(os.readlink(path))


def remove_dir_link(path: Path) -> None:
    """Remove the link at *path* without touching the directory it points to.

    Raises:
        ValueError: *path* is not a directory link.
    """
    if not is_dir_link(path):
        raise ValueError(f"{path} is not a directory link")
    if _IS_WINDOWS:
        os.rmdir(path)
    else:
        path.unlink()
```

`Path.is_junction` exists from Python 3.12. If the floor is lower, add a `_is_junction(path)` helper that reads `os.lstat(path).st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT`, and test it. Check `requires-python` in `pyproject.toml` first.

- [ ] **Step 4: Run** the sushicore suite and the hub suite (`cd D:/Projects/sushistack/cli && PYTHONPATH=D:/Projects/sushicore python -m pytest -q`). Changelog line: `- 2026-09-25 — provision: Added directory links, junctions on Windows and symlinks elsewhere (`sushicore/provision/links.py`).`

Acceptance: both suites green, and the Windows junction test passes on this machine.

---

### Task 2: The migration engine

**Files:**
- Create: `D:/Projects/sushicore/sushicore/provision/migrate.py`
- Test: `D:/Projects/sushicore/tests/provision/test_migrate.py`

**Interfaces:**
- Consumes: Task 1's link functions; `ProvisionLock`, `LockTimeout` from `provision.lock`.
- Produces:
  - `@dataclass(frozen=True) class Move: name: str; source: Path; target: Path; files: int; bytes: int`
  - `@dataclass(frozen=True) class MigrationPlan: old_root: Path; new_root: Path; moves: tuple[Move, ...]; total_bytes: int; free_bytes: int`, with `enough_space` (a property: `free_bytes >= total_bytes * 1.1`) and `already_migrated` (a property: `old_root` is a link to `new_root`).
  - `class MigrationError(RuntimeError)`
  - `plan(old_root: Path, new_root: Path) -> MigrationPlan`. Raises `MigrationError` on a name collision in `new_root`.
  - `migrate(plan: MigrationPlan, report: Callable[[str], None]) -> None`
  - `rollback(old_root: Path, new_root: Path, report: Callable[[str], None]) -> None`
  - `finalize(old_root: Path, report: Callable[[str], None]) -> None`
  - Constants: `JOURNAL = ".migrate-journal.jsonl"`, `ASIDE_SUFFIX = ".pre-migrate"`.

The algorithm, in order:
1. `plan`: each top-level directory of `old_root` is one `Move`, with file count and byte total from a walk. Directory links inside are counted as links, not followed. A name that already exists in `new_root` is a collision; `.lock`, `registry.toml` and `JOURNAL` are not.
2. `migrate` holds `ProvisionLock(new_root / ".lock")`. It refuses when `already_migrated` is true (it reports "already migrated" and returns), and when `enough_space` is false (it raises with both numbers).
3. Per move: journal `{"step":"copy-start","name":…}`. Copy into `new_root/<name>.partial` with `shutil.copytree(symlinks=True)`, then verify that the file count and the size of every file match the source. On a mismatch, delete the `.partial` directory, journal `copy-failed` and raise. On success, rename `.partial` to `<name>` and journal `copied`. A move already journaled `copied` is skipped on re-run, and a leftover `.partial` is deleted first.
4. After every move is `copied`: rename `old_root` to `old_root + ASIDE_SUFFIX` (same volume) and journal `aside`. Then call `make_dir_link(old_root, new_root)` and journal `linked`. If making the link fails, rename the aside copy back and raise.
5. `rollback`: read the journal in reverse. `linked` removes the link. `aside` renames the aside copy back. `copied` deletes `new_root/<name>`. Finally, delete the journal. With no journal, it reports "nothing to roll back" and returns.
6. `finalize` refuses unless `old_root` is a link and the aside copy exists. It then deletes the aside copy, journals `finalized`, and renames the journal to `.migrate-journal.done.jsonl`, so `rollback` has nothing to replay.

- [ ] **Step 1: Failing tests** in `tests/provision/test_migrate.py`. Each test builds a real temporary tree: `old/toolchains/llvm-sycl/bin/clang++.exe`, `old/vcpkg/installed/x.lib` and `old/tools/cmake/bin/cmake.exe`. Tests, each with a verb-first name:
  - `test_plan_counts_files_and_bytes_per_component`
  - `test_plan_rejects_a_name_already_in_the_target`
  - `test_plan_ignores_lock_and_registry_in_the_target`
  - `test_migrate_copies_everything_and_links_the_old_path`: afterwards `old` is a link, `old/tools/cmake/bin/cmake.exe` reads the same bytes, and `old.pre-migrate` exists.
  - `test_migrate_refuses_when_space_is_short` (monkeypatch `shutil.disk_usage`)
  - `test_migrate_reports_already_migrated_and_changes_nothing`
  - `test_interrupted_copy_resumes_without_recopying_finished_components` (monkeypatch `shutil.copytree` to raise `KeyboardInterrupt` on `vcpkg`, re-run, then assert that `copytree` was called once for `toolchains` over both runs)
  - `test_verify_failure_stops_before_the_swap_and_leaves_old_untouched` (monkeypatch the verifier to report a mismatch)
  - `test_rollback_after_success_restores_the_original_tree`: `old` is a real directory with the same files, and `new` has no migrated components.
  - `test_rollback_after_an_interrupted_copy_restores_the_original_tree`
  - `test_finalize_deletes_the_aside_copy_and_rollback_then_has_nothing`
  - `test_finalize_refuses_before_migration_and_deletes_nothing`

- [ ] **Step 2: Run.** Expected: FAIL.

- [ ] **Step 3: Implement** `migrate.py` to the interface and the algorithm above. Keep one small function per step: `_walk_totals`, `_copy_component`, `_verify_component`, `_swap_and_link`, `_journal_append`, `_journal_read`. The report callback is the only output; the module never imports a console.

- [ ] **Step 4: Run** the sushicore and hub suites. Changelog line: `- 2026-09-25 — provision: Added a journaled dependency-root migration with rollback and finalize (`sushicore/provision/migrate.py`).`

Acceptance: every test above passes on Windows with real junctions.

---

### Task 3: Seed the registry from a migrated tree

**Files:**
- Modify: `D:/Projects/sushicore/sushicore/provision/registry.py`
- Test: `D:/Projects/sushicore/tests/provision/test_registry.py`

**Interfaces:**
- Produces: `Registry.seed_from_tree(root: Path, consumer: str, source: str = "migrated") -> list[Component]`. It adds one component per `toolchains/<name>` and `tools/<name>`, plus `vcpkg` and each `ur/<name>` found under `root`. The version comes from `.sushi_toolchain.json` when present, else `"unversioned"`. Components already recorded are skipped. It returns what it added. It does not save; the caller calls `save()`.

- [ ] **Step 1: Failing tests** (read `test_registry.py` for its fixtures first):

```python
def test_seed_records_each_component_with_its_stamp_version(tmp_path):
    root = tmp_path / "root"
    (root / "toolchains" / "llvm-sycl").mkdir(parents=True)
    (root / "toolchains" / "llvm-sycl" / ".sushi_toolchain.json").write_text('{"version": "2026-07-28"}')
    (root / "tools" / "cmake").mkdir(parents=True)
    (root / "vcpkg").mkdir()
    reg = Registry(root / "registry.toml")
    added = reg.seed_from_tree(root, consumer="hub")
    names = {(c.name, c.version) for c in added}
    assert ("llvm-sycl", "2026-07-28") in names
    assert ("cmake", "unversioned") in names
    assert ("vcpkg", "unversioned") in names


def test_seed_skips_components_already_recorded(tmp_path):
    root = tmp_path / "root"
    (root / "vcpkg").mkdir(parents=True)
    reg = Registry(root / "registry.toml")
    reg.seed_from_tree(root, consumer="hub")
    assert reg.seed_from_tree(root, consumer="hub") == []
```

Read the real stamp's keys from `D:/Projects/sushistack/dependencies/toolchains/llvm-sycl/.sushi_toolchain.json`, and use its version key in place of `"version"` if it differs.

- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement**, reusing `Component` and `add`, and `provision.toolchains.stamp` for reading stamps.
- [ ] **Step 4: Run** the sushicore and hub suites. Changelog line: `- 2026-09-25 — provision: Added registry seeding from an existing dependency tree (`sushicore/provision/registry.py`).` Bump `pyproject.toml` to `0.7.0` in this task.

Acceptance: both suites green.

---

### Task 4: `hub migrate` and the root switch

**Files:**
- Create: `D:/Projects/sushistack/cli/sushihub/services/migrate.py` (hub-side composition: resolves the old and new roots, renders the plan, calls sushicore, seeds and saves the registry after success)
- Modify: `D:/Projects/sushistack/cli/sushihub/cli.py` (a `migrate` command in the dependencies help panel)
- Modify: `D:/Projects/sushistack/cli/sushihub/config.py` `deps_dir()`
- Modify: `D:/Projects/sushistack/cli/pyproject.toml` (`sushicore>=0.7.0`)
- Test: `D:/Projects/sushistack/cli/tests/test_migrate_command.py`
- Docs: hub's README or CLI guide section for `hub migrate`, and hub's CHANGELOG

**Interfaces:**
- `hub migrate [--dry-run] [--rollback] [--finalize] [--yes]`:
  - `--dry-run` prints the plan: each component with its file count and size, the total, free space on the target, "enough space: yes/no", and the exact old and new paths. It then exits 0 without touching disk.
  - A plain run shows the same plan and asks for confirmation unless `--yes` is passed. It then migrates, seeds the registry with consumer `hub` and saves it.
  - `--rollback` and `--finalize` call the sushicore functions.
- `deps_dir()`: the `SUSHISTACK_DEPS_DIR` override still wins. Otherwise, when `<workspace>/dependencies` is a directory link (`is_dir_link`), it returns `provision.home.default_root()`. Else it returns `<workspace>/dependencies`, as today.

- [ ] **Step 1: Failing tests.** Use temporary workspaces and monkeypatch `home.default_root` to a temporary directory:
  - `--dry-run` prints every component and changes nothing.
  - A real run with `--yes` leaves `dependencies` as a link and writes `registry.toml` with the components.
  - `deps_dir()` returns the provision root after migration and the workspace path before it.
  - `--rollback` restores `deps_dir()` to the workspace path.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement.** In `services/migrate.py`, keep the plan rendering as a function of its own, separate from the confirmation prompt.
- [ ] **Step 4: Run** `cd D:/Projects/sushistack/cli && PYTHONPATH=D:/Projects/sushicore python -m pytest -q`. Then run the real `hub migrate --dry-run` against the live workspace, which is read-only, and paste its output. Also run `hub doctor`. It must still say "Inventory complete" before the real move.

Acceptance: the hub suite is green, and the live `hub migrate --dry-run` lists `build`, `toolchains`, `tools`, `ur` and `vcpkg` with "enough space: yes".

---

### Task 5: Owner gate — the real move

The controller shows the owner the live `hub migrate --dry-run` output and the list of files that name the old path (from the inventory: build trees of sushiai, sushiblas, sushidsp, sushiengine, sushifx and sushiruntime; `sushistack/.sushistack/workspace.toml`; `sushiengine/cli/config.local.toml`; `sushiruntime/cli/config.local.toml`). The junction keeps all of them working, and none is edited.

The owner:
1. Pauses SushiEngine work, and closes IDEs and terminals that hold files under `D:\Projects\sushistack\dependencies` (a locked file fails verification, and nothing is lost).
2. Runs `hub migrate`, reads the plan and confirms.
3. Keeps `D:\Projects\sushistack\dependencies.pre-migrate` until Task 6 passes.

Acceptance: `hub migrate` prints success, `dir D:\Projects\sushistack` shows `dependencies` as `<JUNCTION>`, and `C:\Users\sushi\.sushisystems` holds the five components.

---

### Task 6: Controller verification, then finalize on the owner's word

The controller runs, and pastes every output:
- `hub doctor` and `hub install --dry-run`: the same components as the pre-move baseline, now under `C:\Users\sushi\.sushisystems`.
- `sd doctor`, `st doctor`, `sr doctor`, `se doctor`, `sa doctor`, `sb doctor` (each where the CLI has one).
- A real build of each module through its own CLI: `sr build`, `sa build`, `sb build`, `sd build`, `st build`, and `se build` last, only with the owner's go-ahead since SushiEngine is paused.

If every build passes, the owner runs `hub migrate --finalize`, which deletes the 20 GB aside copy on D:. If anything fails, the owner runs `hub migrate --rollback`: two renames, instant, and nothing is copied.

Acceptance: all builds green, and the owner decides between finalize and rollback.

---

## Out of scope (recorded for the backlog)

- Rewriting configs and build caches to the new path, and removing the junction (spec phase B step 6).
- The versioned layout `toolchains/<name>/<version>/`.
- Pruning `vcpkg/buildtrees` and `vcpkg/downloads` (part of the 17 GB).
