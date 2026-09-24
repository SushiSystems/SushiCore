# Module adoption (sub-project 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `st` and `sd` gain `setup`, `doctor`, `link` and `unlink` from `sushicore.provision`, and `st` drops its private copies of process, discovery, CMake and build-environment code for the sushicore ones.

**Architecture:** sushicore gains a link pointer (a module records which workspace it is linked to in its own `cli/config.local.toml`) and `ModuleConfig` reads the linked workspace's `[tool]` table at load time, so linking copies nothing. Provision messages name the calling program instead of `hub`. `sd` registers the shared commands and loses its hand-written `setup`. `st` splits its config into its own sections plus a `ToolSettings` loaded through `ModuleConfig`, then swaps its internals for sushicore's, then registers the shared commands with its own checks.

**Tech Stack:** Python 3.10+, Typer, pytest, `sushicore` (editable, `D:/Projects/sushicore`).

**Spec:** `D:/Projects/sushicore/docs/agent/specs/2026-09-23-provision-design.md` (sub-project 3, "Module commands", "Doctor").

## Global Constraints

- Nothing on the owner's machine breaks. `st`, `sd`, `hub`, `sr`, `se`, `sa`, `sb` keep working after every commit, because every CLI runs from its live working tree.
- Hub's dependency tree does not move. `~/.sushisystems` migration (phase B) is out of scope.
- `sushicore` version becomes `0.6.0`; `st` and `sd` require `sushicore>=0.6.0`.
- Owner decisions 2026-09-24, overriding any draft text below: P2 is `Runner(..., catch_interrupt: bool = False)`, default off so sr/se/sa/sb/sd/hub keep today's behaviour and only st passes True; P6 moves st's vcvars locator (vswhere, then disk scan, VS 2019/2022/2026) into `sushicore.provision.probe`, and hub's probe output on this machine must stay identical; deploy's file lookups go to st's own `sushitrack_cli/services/artifacts.py`; `ToolSettings.generator` defaults to `""` and a linked workspace's `[tool] generator` wins when present; `capture` returns `(code, stdout, stderr)`; st files touched get the Apache header; the four small visible changes the draft lists are accepted.
- Linking copies nothing: the workspace's `[tool]` is layered at load time (owner decision, 2026-09-24).
- Implementers never commit, stash, checkout, reset or create worktrees; the controller commits per task by path.
- `D:/Projects/sushidsp` has the owner's uncommitted work outside `cli/` (including `docs/reference/CHANGELOG.md`). Never touch those files' existing hunks; the controller stages only this plan's hunk (`git apply --cached`).
- No subagent runs `st build`, `st test`, `sd build`, cmake, ninja or ctest. The controller runs builds after each wave.
- Python files open with the repo's license header and a module docstring; every function has a Google-style docstring whose summary is one sentence starting with a verb.
- Changelog lines: `- 2026-09-24 — <area>: <Past-tense verb> <what> (`paths`).`, one sentence, at most 240 characters.

## Review Focus

1. `st link` from a SushiTrack checkout outside any workspace, with no `--workspace` and no `SUSHISTACK_HOME`: exits 2 with the no-workspace message, writes nothing. (Task 3 test.)
2. A link pointer naming a workspace that was later deleted: config loading ignores it and falls back to the walk-up, no crash. (Task 3 test.)
3. `st config`, `st env`, `st build` defaults unchanged after the config split: Windows generator still Ninja, elsewhere empty; `ST_CMAKE`/`ST_CTEST`/`ST_GENERATOR` still honoured. (Task 5 test.)
4. `sd setup` inside a workspace no longer shells out to `hub`; it provisions into the shared root and says so. (Task 4 test.)
5. `st doctor --for infer` on a machine without torch: exit 1, rows name `pip install` fixes, other groups not run. (Task ST-DOCTOR test.)

---

## Waves

| Wave | Tasks | Repos / files | Waits on | Controller build after |
| --- | --- | --- | --- | --- |
| 0 | Task 0 (owner) | pip / pipx environments | — | `st --help`, `sd --help` |
| 1 | Task 1, Task 2 | sushicore: `provision/pipeline.py`, `provision/steps.py` / `proc.py` | Task 0 | sushicore pytest; hub pytest |
| 2 | Task 3 | sushicore: `workspace.py`, `module_config.py`, `provision/commands.py`, version | Wave 1 | sushicore pytest; hub pytest; `hub doctor` |
| 3 | Task 4 ∥ Task 5 | sushidsp `cli/` ∥ sushitrack `cli/sushitrack_cli/config.py` + call sites | Wave 2 | sd and st pytest; `sd doctor`; `st build`; `st test` |
| 4 | ST-Tasks 1–8 (serial) | sushitrack `cli/` | Task 5 | st pytest; `st build`; `st test`; `st run --help` |
| 5 | Task ST-DOCTOR | sushitrack `cli/` | Wave 4 | st pytest; `st doctor`; `st setup --dry-run` |
| 6 | ST-Task 9 (delete st's copies) | sushitrack `cli/` | Wave 5 | st pytest; `st build`; `st test` |

---

### Task 0: Owner gate — editable sushicore under `st` and `sd`

The owner runs, from any directory:

```
python -m pip install --user -e D:\Projects\sushicore
pipx runpip sushidsp-cli install -e D:\Projects\sushicore
```

Acceptance: `python -c "import sushicore.provision"` succeeds, `pipx runpip sushidsp-cli show sushicore` reports `Editable project location: D:\Projects\sushicore`, and `st --help` / `sd --help` still open.

---

### Task 1: Provision messages name the calling program

**Files:**
- Modify: `D:/Projects/sushicore/sushicore/provision/pipeline.py` (`InstallContext`)
- Modify: `D:/Projects/sushicore/sushicore/provision/steps.py` (messages at the `hub remove --all`, `hub install`, `hub install --customize` lines)
- Test: `D:/Projects/sushicore/tests/provision/test_steps.py`

**Interfaces:**
- Produces: `InstallContext.program: str = "hub"` — the command a user types to re-run provisioning. Task 3 passes `module.profile.program`.

Toolchain installer hints (`toolchains/adaptivecpp.py`, `toolchains/intel_llvm.py`) stay as they are: only hub's non-empty `ToolchainSelection` reaches them.

- [ ] **Step 1: Write the failing test** — append to `tests/provision/test_steps.py`, reusing that file's existing fakes for a source with one missing required dependency and a manager that cannot install it (read the file first and use its helper names):

```python
def test_missing_dependency_hint_names_the_calling_program(capsys_console):
    """Assert the re-run hint names the program in the context, not hub."""
    ctx = _context(program="st")
    _run_detect_with_one_missing(ctx)
    assert "`st setup`" in capsys_console.text()
    assert "hub install" not in capsys_console.text()


def test_missing_dependency_hint_defaults_to_hub(capsys_console):
    """Assert a context built without a program keeps hub's wording."""
    ctx = _context()
    _run_detect_with_one_missing(ctx)
    assert "`hub install`" in capsys_console.text()
```

If the file has no `capsys_console`/`_context`/`_run_detect_with_one_missing` helpers, add them at the top of the test module built on the file's existing console binding and fakes.

- [ ] **Step 2: Run** `cd D:/Projects/sushicore && python -m pytest tests/provision/test_steps.py -q` — expected FAIL (`InstallContext` has no `program`).

- [ ] **Step 3: Implement.** In `pipeline.py` add to `InstallContext`, after `consumer`:

```python
    program: str = "hub"
```

In `steps.py`, add one helper beside the other module-level helpers:

```python
def _rerun_command(ctx: InstallContext) -> str:
    """Return the command that re-runs provisioning for the program in *ctx*."""
    return "hub install" if ctx.program == "hub" else f"{ctx.program} setup"
```

Replace the three literals: `` `hub install` `` → `` f"`{_rerun_command(ctx)}`" ``; `` `hub install --customize` `` → keep literally only when `ctx.program == "hub"`, else drop the `--customize` sentence; `` (`hub remove --all` does it for you) `` → keep only when `ctx.program == "hub"`. Hub's output must stay byte-identical.

- [ ] **Step 4: Run** `python -m pytest -q` in sushicore (all pass) and `cd D:/Projects/sushistack/cli && PYTHONPATH=D:/Projects/sushicore python -m pytest -q` (280 pass).

Acceptance: both suites green; `hub install --dry-run` output identical to before.

---

### Task 2: sushicore process helpers st needs

**Files:** defined by the "sushicore prerequisite" section of the drafted st-internals tasks (spliced below as part of this task): `D:/Projects/sushicore/sushicore/proc.py`, `D:/Projects/sushicore/tests/test_proc.py`.

Acceptance: sushicore and hub suites green; every existing `Runner` test unchanged.

---

### Task 3: Link pointer and load-time layering

**Files:**
- Modify: `D:/Projects/sushicore/sushicore/workspace.py`
- Modify: `D:/Projects/sushicore/sushicore/module_config.py` (`workspace_home`)
- Modify: `D:/Projects/sushicore/sushicore/provision/commands.py` (`link`, `unlink`, `setup`'s `InstallContext`)
- Modify: `D:/Projects/sushicore/pyproject.toml` (version `0.6.0`), `D:/Projects/sushicore/README.md` (Provisioning section), `D:/Projects/sushicore/docs/reference/CHANGELOG.md`
- Test: `D:/Projects/sushicore/tests/test_workspace_link.py` (new), `D:/Projects/sushicore/tests/test_module_config.py`, `D:/Projects/sushicore/tests/provision/test_commands.py`

**Interfaces:**
- Produces in `sushicore.workspace`:
  - `LINK_SECTION = "link"`
  - `read_link(config_dir: Path) -> Path | None` — the `workspace` value of `[link]` in `config_dir / "config.local.toml"`, or None when absent or when that directory has no `WORKSPACE_MARKER`.
  - `write_link(config_dir: Path, workspace: Path) -> Path` — merges `[link] workspace = "<posix abs path>"` into that file, preserving every other table; returns the file.
  - `clear_link(config_dir: Path) -> bool` — removes `[link]`; deletes the file when nothing else remains; returns whether a pointer existed.
- `ModuleConfig.workspace_home()` precedence becomes: `SUSHISTACK_HOME` → `read_link(self.config_dir(root))` → walk-up.
- `link` writes both the `[modules]` record and the pointer; `unlink` removes both. `setup` passes `program=module.profile.program`.

- [ ] **Step 1: Write the failing tests.** `tests/test_workspace_link.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the module-side link pointer."""

from __future__ import annotations

from sushicore.workspace import WORKSPACE_MARKER, clear_link, read_link, read_toml, write_link


def _workspace(tmp_path):
    """Create a directory carrying the workspace marker and return it."""
    ws = tmp_path / "ws"
    (ws / WORKSPACE_MARKER).mkdir(parents=True)
    return ws


def test_write_then_read_returns_the_workspace(tmp_path):
    """Assert a written pointer reads back as the same workspace."""
    ws = _workspace(tmp_path)
    cfg = tmp_path / "mod" / "cli"
    cfg.mkdir(parents=True)
    write_link(cfg, ws)
    assert read_link(cfg) == ws.resolve()


def test_write_keeps_other_tables(tmp_path):
    """Assert writing the pointer leaves an existing [tool] table intact."""
    ws = _workspace(tmp_path)
    cfg = tmp_path / "cli"
    cfg.mkdir()
    (cfg / "config.local.toml").write_text('[tool]\ncmake_exe = "C:/cmake.exe"\n')
    write_link(cfg, ws)
    doc = read_toml(cfg / "config.local.toml")
    assert doc["tool"]["cmake_exe"] == "C:/cmake.exe"
    assert "workspace" in doc["link"]


def test_read_ignores_a_pointer_to_a_deleted_workspace(tmp_path):
    """Assert a pointer whose target lost its marker reads as no link."""
    ws = _workspace(tmp_path)
    cfg = tmp_path / "cli"
    cfg.mkdir()
    write_link(cfg, ws)
    (ws / WORKSPACE_MARKER).rmdir()
    assert read_link(cfg) is None


def test_clear_removes_the_file_when_nothing_else_remains(tmp_path):
    """Assert clearing the only table deletes the file and reports a pointer existed."""
    ws = _workspace(tmp_path)
    cfg = tmp_path / "cli"
    cfg.mkdir()
    write_link(cfg, ws)
    assert clear_link(cfg) is True
    assert not (cfg / "config.local.toml").exists()
    assert clear_link(cfg) is False
```

Append to `tests/test_module_config.py` (reuse its profile fixture; read the file first):

```python
def test_workspace_home_follows_the_link_pointer(tmp_path, monkeypatch):
    """Assert a linked module outside the workspace tree finds its workspace."""
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    ws = tmp_path / "ws"
    (ws / WORKSPACE_MARKER).mkdir(parents=True)
    mod = tmp_path / "elsewhere" / "mod"
    (mod / "cli").mkdir(parents=True)
    (mod / "CMakeLists.txt").write_text("")
    write_link(mod / "cli", ws)
    assert ModuleConfig(_profile()).workspace_home(mod) == ws.resolve()


def test_environment_beats_the_link_pointer(tmp_path, monkeypatch):
    """Assert SUSHISTACK_HOME still wins over a recorded link."""
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.setenv("SUSHISTACK_HOME", str(other))
    ws = tmp_path / "ws"
    (ws / WORKSPACE_MARKER).mkdir(parents=True)
    mod = tmp_path / "mod"
    (mod / "cli").mkdir(parents=True)
    (mod / "CMakeLists.txt").write_text("")
    write_link(mod / "cli", ws)
    assert ModuleConfig(_profile()).workspace_home(mod) == other
```

Append to `tests/provision/test_commands.py` (reuse its app/profile helpers):

```python
def test_link_writes_record_and_pointer_and_unlink_removes_both(tmp_path, monkeypatch):
    """Assert link records the module in both places and unlink undoes both."""
    ws = tmp_path / "ws"
    (ws / ".sushistack").mkdir(parents=True)
    app, root = _app(tmp_path)
    runner = CliRunner()
    assert runner.invoke(app, ["link", "--workspace", str(ws)]).exit_code == 0
    assert read_link(root / "cli") == ws.resolve()
    assert registered_modules(ws)
    assert runner.invoke(app, ["unlink", "--workspace", str(ws)]).exit_code == 0
    assert read_link(root / "cli") is None
    assert not registered_modules(ws)


def test_link_outside_any_workspace_exits_2_and_writes_nothing(tmp_path, monkeypatch):
    """Assert link with no resolvable workspace fails without touching disk."""
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    app, root = _app(tmp_path)
    result = CliRunner().invoke(app, ["link"])
    assert result.exit_code == 2
    assert not (root / "cli" / "config.local.toml").exists()
```

(If `_app` does not exist, add a helper returning a Typer app with `register_provision_commands` over a `ModuleProvision` rooted at a temp checkout with a `cli/` directory.)

- [ ] **Step 2: Run** `python -m pytest tests/test_workspace_link.py tests/test_module_config.py tests/provision/test_commands.py -q` — expected FAIL (`read_link` undefined).

- [ ] **Step 3: Implement** in `workspace.py`, below `remove_module`:

```python
#: Table in a module's ``config.local.toml`` naming the workspace it is linked to.
LINK_SECTION = "link"

#: File in a module's config directory that carries the link pointer.
_LOCAL_CONFIG = "config.local.toml"


def read_link(config_dir: Path) -> Path | None:
    """Return the workspace this module is linked to, or None when unlinked or stale."""
    table = read_toml(config_dir / _LOCAL_CONFIG).get(LINK_SECTION) or {}
    raw = table.get("workspace")
    if not raw:
        return None
    target = Path(raw)
    return target if (target / WORKSPACE_MARKER).exists() else None


def write_link(config_dir: Path, workspace: Path) -> Path:
    """Record *workspace* as this module's linked workspace and return the file written."""
    path = config_dir / _LOCAL_CONFIG
    doc = read_toml(path)
    doc[LINK_SECTION] = {"workspace": workspace.resolve().as_posix()}
    _write_toml(path, doc)
    return path


def clear_link(config_dir: Path) -> bool:
    """Remove this module's link pointer and report whether one existed."""
    path = config_dir / _LOCAL_CONFIG
    doc = read_toml(path)
    if LINK_SECTION not in doc:
        return False
    del doc[LINK_SECTION]
    if doc:
        _write_toml(path, doc)
    else:
        path.unlink()
    return True
```

Use the TOML writer `write_module` already uses for `_write_toml` (read `workspace.py`; if it writes through a helper, reuse it; if it formats inline, extract that formatting into `_write_toml(path, doc)` and have `write_module`/`remove_module` call it, keeping their output byte-identical — `tests/test_workspace_modules.py` pins it).

In `module_config.py` `workspace_home`, between the env check and the walk-up:

```python
        try:
            start = root or self.find_project_root()
        except SystemExit:
            return None
        linked = read_link(self.config_dir(start))
        if linked is not None:
            return linked
        return walk_up(start, has_marker(WORKSPACE_MARKER))
```

In `provision/commands.py`: `link` calls `write_link(root / "cli", target)` after `write_module`; `unlink` calls `clear_link(root / "cli")` after `remove_module`; `setup`'s `InstallContext(...)` gains `program=module.profile.program`. Bump `pyproject.toml` version to `0.6.0`. README Provisioning section: one paragraph saying `link` records the module in the workspace and a `[link]` pointer in the module's `cli/config.local.toml`, and that config loading layers the linked workspace's `[tool]` at read time. CHANGELOG: `- 2026-09-24 — workspace: Added a module-side link pointer that config loading follows to the linked workspace (`workspace.py`, `module_config.py`, `provision/commands.py`).`

- [ ] **Step 4: Run** sushicore full suite, hub suite (`PYTHONPATH=D:/Projects/sushicore`), and `hub doctor`.

Acceptance: all green; `hub doctor` still "Inventory complete".

---

### Task 4: `sd` adopts the shared commands

**Files:**
- Modify: `D:/Projects/sushidsp/cli/sushidsp/config.py` (`Config` base, `bundled_clang`, `compiler_source`)
- Modify: `D:/Projects/sushidsp/cli/sushidsp/cli.py` (drop the `setup` command and `setup_svc` import; register shared commands)
- Delete: `D:/Projects/sushidsp/cli/sushidsp/services/setup.py`, `D:/Projects/sushidsp/cli/tests/test_setup.py`
- Create: `D:/Projects/sushidsp/cli/tests/test_provision_commands.py`
- Modify: `D:/Projects/sushidsp/cli/pyproject.toml` (`sushicore>=0.6.0`)
- Docs: the `sd setup` section of `D:/Projects/sushidsp/docs/` wherever `grep -rn "sd setup" D:/Projects/sushidsp/docs D:/Projects/sushidsp/README.md` finds it (skip files listed dirty in `git -C D:/Projects/sushidsp status --short`; report them instead); changelog line handed to the controller in the report, not written.

**Interfaces:**
- Consumes: `ModuleProvision`, `register_provision_commands` (sushicore), `ProvisionSettings`, `sushicore.provision.home.search_roots() -> list[Path]`.

- [ ] **Step 1: Failing test** `tests/test_provision_commands.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests that sd carries the shared provision commands."""

from __future__ import annotations

from typer.testing import CliRunner

from sushicore.provision.config import ProvisionSettings
from sushidsp.cli import app
from sushidsp.config import Config


def test_sd_registers_the_four_provision_commands():
    """Assert setup, doctor, link and unlink appear in sd's help."""
    out = CliRunner().invoke(app, ["--help"]).output
    for name in ("setup", "doctor", "link", "unlink"):
        assert name in out


def test_setup_no_longer_takes_install():
    """Assert the old --install flag is gone in favour of --dry-run."""
    out = CliRunner().invoke(app, ["setup", "--help"]).output
    assert "--dry-run" in out
    assert "--install" not in out


def test_config_is_a_provision_config():
    """Assert sd's config carries every field provision reads."""
    assert issubclass(Config, ProvisionSettings)


def test_bundled_clang_is_found_under_the_provision_root(tmp_path, monkeypatch):
    """Assert a clang++ under the provision root's toolchains is picked up."""
    monkeypatch.setenv("SUSHISYSTEMS_HOME", str(tmp_path))
    exe_name = Config()._clang_name()
    exe = tmp_path / "toolchains" / "llvm-sycl-nightly" / "bin" / exe_name
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    assert Config().bundled_clang() == str(exe)
```

- [ ] **Step 2: Run** `cd D:/Projects/sushidsp/cli && PYTHONPATH=D:/Projects/sushicore python -m pytest tests/test_provision_commands.py -q` — FAIL.

- [ ] **Step 3: Implement.**
  - `config.py`: `from sushicore.provision.config import ProvisionSettings`; `class Config(ProvisionSettings)`; remove the now-inherited `llvm_root` field declaration; in `bundled_clang` build candidates as: explicit `llvm_root`, then `root / "toolchains" / name` for each `root` in `sushicore.provision.home.search_roots()` and each bundle name, then the existing workspace `dependencies/toolchains` candidates; `compiler_source`'s last string names `` `sd setup` `` instead of `` `hub install` ``. Docstrings follow the global rule.
  - `cli.py`: delete the `setup` command and the `setup_svc` import; after the other commands:

```python
register_provision_commands(app, ModuleProvision(
    profile=PROFILE,
    project_root=find_project_root,
    load_config=load_config,
    console=lambda: console,
))
```

with `from sushicore.provision.commands import ModuleProvision, register_provision_commands`, `from . import console`, `from .config import PROFILE, find_project_root, load_config`.
  - Delete `services/setup.py` and `tests/test_setup.py`. Bump the sushicore floor.

- [ ] **Step 4: Run** the sd suite; then `sd --help`, `sd doctor`, `sd setup --dry-run`, `sd config` and paste outputs.

Acceptance: sd suite green; `sd doctor` renders the Doctor table; `sd config` unchanged except the compiler-source hint.

---

### Task 5: `st` config split (ST-CONFIG)

**Files:**
- Modify: `D:/Projects/sushitrack/cli/sushitrack_cli/config.py`
- Modify: `D:/Projects/sushitrack/cli/config.toml` (move `[build] cmake/ctest/generator` and `[platform.windows.build] generator` into `[tool]` / `[tool.windows]`)
- Modify: every read of `cfg.build_cmake`, `cfg.build_ctest`, `cfg.build_generator` (currently `services/build.py`, `services/tests.py`, `services/diag.py`) to `cfg.tool.cmake_exe or "cmake"`, `cfg.tool.ctest_exe or "ctest"`, `cfg.tool.generator` — one-line edits only
- Modify: `D:/Projects/sushitrack/.gitignore` (add `cli/config.local.toml`)
- Test: `D:/Projects/sushitrack/cli/tests/test_config.py`

**Interfaces:**
- Produces: `sushitrack_cli.config.ToolSettings(ProvisionSettings)`; `Config.tool: ToolSettings`; `load_config(root=None)` fills `tool` via `ModuleConfig(PROFILE, use_workspace_config=True).load(ToolSettings)` when a checkout is found, else `ToolSettings()` with env overrides applied; `load_tool(root=None) -> ToolSettings` for provision's `load_config`.
- Env names: `ST_CMAKE`, `ST_CTEST`, `ST_GENERATOR` keep working, mapped onto `cmake_exe`, `ctest_exe`, `generator` through `PROFILE`'s `extra_env_overrides`.

- [ ] **Step 1: Failing tests** appended to `tests/test_config.py` (use its existing checkout fixture; read it first):

```python
def test_tool_settings_carry_the_platform_generator(st_checkout, monkeypatch):
    """Assert the split config keeps Ninja on Windows and CMake's default elsewhere."""
    cfg = load_config(st_checkout)
    expected = "Ninja" if IS_WINDOWS else ""
    assert cfg.tool.generator == expected


def test_legacy_environment_names_still_override(st_checkout, monkeypatch):
    """Assert ST_CMAKE, ST_CTEST and ST_GENERATOR still reach the tool settings."""
    monkeypatch.setenv("ST_CMAKE", "C:/x/cmake.exe")
    monkeypatch.setenv("ST_CTEST", "C:/x/ctest.exe")
    monkeypatch.setenv("ST_GENERATOR", "Unix Makefiles")
    tool = load_config(st_checkout).tool
    assert (tool.cmake_exe, tool.ctest_exe, tool.generator) == (
        "C:/x/cmake.exe", "C:/x/ctest.exe", "Unix Makefiles")


def test_config_no_longer_has_build_tool_fields():
    """Assert the tool fields moved out of the sectioned config."""
    names = {f.name for f in fields(Config)}
    assert not names & {"build_cmake", "build_ctest", "build_generator"}


def test_tool_settings_are_a_provision_config():
    """Assert st's tool settings carry every field provision reads."""
    assert issubclass(ToolSettings, ProvisionSettings)
```

- [ ] **Step 2: Run** `cd D:/Projects/sushitrack/cli && PYTHONPATH=D:/Projects/sushicore python -m pytest tests/test_config.py -q` — FAIL.

- [ ] **Step 3: Implement.** In `config.py`:
  - `PROFILE` gains `extra_env_overrides={"cmake_exe": "ST_CMAKE", "ctest_exe": "ST_CTEST", "generator": "ST_GENERATOR"}` (check `ModuleProfile.env_overrides()` merges `extra_env_overrides`; if it does not, report and stop).
  - `_MODULE = ModuleConfig(PROFILE, use_workspace_config=True)`.
  - `class ToolSettings(ProvisionSettings)` with `generator: str = ""` (st's default; Windows gets Ninja from `[tool.windows]`).
  - Remove `build_cmake`, `build_ctest`, `build_generator` from `Config` and `ENV_OVERRIDES`; add `tool: ToolSettings = field(default_factory=ToolSettings)`.
  - `load_tool(root=None)`: returns `_MODULE.load(ToolSettings)` when `config_dir(root)` resolves, else a `ToolSettings()` with `platform` set and env overrides applied through sushicore's loader over an empty source list.
  - `load_config` sets `cfg.tool = load_tool(root)`.
  - `config.toml`: remove `cmake`, `ctest`, `generator` from `[build]` and the `[platform.windows.build]` table; add:

```toml
[tool]
cmake_exe = ""
ctest_exe = ""
generator = ""

[tool.windows]
generator = "Ninja"
```

  - Update the three call sites. `st config`'s table (`diag.config_show`) must list the `tool` fields too: extend its rows with `tool.<name>` for each `ToolSettings` field (source column `tool`).

- [ ] **Step 4: Run** st suite; `st config`, `st env` and paste. Controller then runs `st build` and `st test`.

Acceptance: st suite green; `st build` configures with the same generator and build dir as before.

---

## st internals (Wave 4; its "Sushicore prerequisite" section is Task 2)

# st internals onto sushicore: plan tasks

Sub-project 3 of `D:/Projects/sushicore/docs/agent/specs/2026-09-23-provision-design.md`: `st`
drops `proc.py`, `services/discovery.py`, its own CMake driving and its vcvars snapshot for the
sushicore bricks `sd` already uses. These tasks are written against the Config shape Task
ST-CONFIG produces (`cfg.tool: ToolSettings`, `build_cmake`/`build_ctest`/`build_generator`
removed).

Preconditions, outside this file:

- Task ST-CONFIG has landed.
- The sushicore prerequisites below (P1 to P6) have landed and are released to the version st pins.
- The `st doctor` replacement has landed before Task 9, because `diag.doctor` is the last caller
  of `proc.tool_version`, `build_svc.cmake_exe`, `test_svc.ctest_exe` and `env.find_vcvars`.
  If it has not, Task 9 cannot delete `proc.py` and waits.

## Replacement table

| st file / function | sushicore replacement | Behavioural difference | Resolution |
| --- | --- | --- | --- |
| `proc.run(cmd, cwd, env, echo)` | `Runner.run(cmd, cwd, env)` | Missing exe: st returns 127, sushicore returns 1. Message text differs (st names `cli/config.local.json`, sushicore names `config.local.toml`). | P2: `Runner(..., missing_exit_code=1)` keyword; st passes 127. Message: accept sushicore's (st's names a file that no longer exists). |
| same | same | Ctrl+C: st warns "Interrupted." and returns 130; sushicore lets `KeyboardInterrupt` propagate. | P2: Runner catches it, warns, returns 130, for every CLI. **Owner decision** (changes sr/se/sa/sb/sd too). |
| same | same | Echo on Linux: st uses `shlex.join`, sushicore `list2cmdline`. Only quoting of arguments with spaces or quotes differs. | Accept sushicore's. **Owner decision** if the echoed line on Linux counts as user-visible behaviour. |
| same | same | `echo=False` and string commands. | No st caller uses either after Task 3 (the vcvars string moves into sushicore). Dropped. |
| `proc.run_drained` | `Runner.run_drained` | sushicore decodes without `errors="replace"`, so non-UTF-8 ctest output raises. `highlight=False, soft_wrap=True` added. Missing exe and Ctrl+C as above. | P3: add `errors="replace"`. The Rich flags are an improvement, kept. |
| `proc.capture` | none | sushicore has no capture. | P1: `Runner.capture(cmd, cwd=None, env=None) -> tuple[int, str, str]`. |
| `proc.which` | `Runner.resolve_exe` | `resolve_exe` returns the bare name when not found, `which` returns None. | Only caller is `diag._git_describe`; it switches to capture's 127 (Task 8). |
| `proc.tool_version`, `proc.format_command` | none | Only `diag.doctor` and `proc` itself use them. | Not needed by st. No prerequisite. |
| `discovery.list_executables`, `match_by_name` | `ExecutableIndex.find`, `.match` | sushicore limits depth to 4; st walks unbounded. st also prunes `.git`. sushicore skips `.lib/.pdb/.dll` suffixes (only matters off Windows). | st builds `ExecutableIndex(skip_dirs=(".git",), max_depth=16)`; both knobs already exist. Suffix list accepted. |
| `runner._select` | `ExecutableIndex.select` | Different table (paths relative to `build.parent`, not `paths.root`), `IntPrompt` re-asks instead of failing, no non-TTY failure. | Keep st's `_select`; only its list comes from `index.find`. |
| `discovery.find_file/find_binary/find_artifact`, `shared_lib_name`, `import_lib_name` | none | sushicore finds executables only, not DLLs or import libs. | Move into a new st module `services/artifacts.py` (Task 2). **Owner decision**: new module name/boundary. |
| `build.cache_value` | `cmake_cache.cached_value` | st matches `name.split(":")[0]`, sushicore matches `entry + ":"`. Same result on every real cache line. | Straight swap. |
| `build.stale_tree` | `cmake_cache.is_stale` | Identical. | Straight swap. |
| `build.cmake_exe(cfg)` | `CMakeDriver.cmake(cfg.tool)` | st default `"cmake"`; sushicore `"cmake"` when `cmake_exe` empty. | Same. |
| `tests.ctest_exe(cfg)` | `CMakeDriver.ctest(cfg.tool)` | Same. | Same. |
| `build.generator(cfg)` | `cfg.tool.generator` | `ToolConfig.generator` defaults to `"Ninja"` on every OS; st defaults to Ninja on Windows and CMake's default elsewhere. | st keeps a one-line policy function over `cfg.tool` (Task 4). It needs `ToolSettings.generator` to default to `""` in ST-CONFIG. **Owner decision** if ST-CONFIG does not already do that, or if a workspace `[tool] generator = "Ninja"` should win on Linux. |
| `build._needs_configure` | `CMakeDriver.needs_configure` | sushicore checks the Makefile sentinel for every non-Ninja generator, so a Visual Studio tree would always reconfigure. st checks a sentinel only for Ninja/Unix Makefiles and adds the `.sushitrack_config` stamp. | st keeps the stamp policy and calls the driver only for sentinel generators (`Ninja`, `Unix Makefiles`, `""`); VS/Xcode use `CMakeCache.txt` + `is_stale`. Warning text is identical. |
| `build.build` compile step | `CMakeDriver.compile` | No `--parallel`. | P4: `jobs: int | None = None`, emitted after `--config`, before targets, matching st's argv. |
| `tests.test` ctest step | `CMakeDriver.ctest_run` | No `--parallel`, no `-C`. Repeat message says "(stop on first failure)" vs st's "(stops on the first failure)". | P5: `jobs` and `config` keywords, appended in st's order. Message: accept sushicore's. |
| `build.clean` | `CMakeDriver.clean_tree` | st removes build and package with its own messages. | Keep st's `clean`. |
| `env.load_build_env(build_dir)` | `build_env.read_cache/write_cache/merge_env` + sd-style composition | Cache now keyed (a cache made by another vcvars is ignored). Device-selection vars dropped from snapshots. | Keyed cache is the fix `test_env.py` already anticipates. Device filter accepted. |
| `env.find_vcvars` (vswhere, then disk scan of every VS year and edition) | `provision.probe` globs VS 2022 only; `snapshot_windows` needs `cfg.vs_vcvars` set | A machine that never ran `st setup`, or runs VS 2019/2026, loses the vcvars snapshot. | P6: move st's locator into `sushicore.provision.probe.find_vcvars()` and add `build_env.snapshot_vcvars(path, console)`. **Owner decision**: this moves code into sushicore's probe. |
| `env._snapshot_windows` skip inside a VS shell (`VSINSTALLDIR`) | none | sushicore snapshots regardless. | st composition checks `VSINSTALLDIR` before snapshotting (Task 3). |
| `env._snapshot_windows` messages | `snapshot_vcvars` messages | "Loading Visual Studio environment from {path}" vs "(vcvars64)...". | P6 prints the path. |

## Sushicore prerequisite

Each lands in sushicore with its own test before st Task 1 starts. Signatures are exact.

**P1. `Runner.capture`** in `sushicore/proc.py`:

```python
def capture(self, cmd: list[str], cwd: Path | None = None,
            env: dict[str, str] | None = None) -> tuple[int, str, str]:
    """Run *cmd* quietly and return its exit code, stdout and stderr."""
```

Resolves `cmd[0]` through `resolve_exe`. Echoes nothing. `capture_output=True, text=True,
errors="replace"`. `FileNotFoundError` returns `(127, "", "Executable not found: '<cmd[0]>'")`
and prints nothing. `KeyboardInterrupt` warns "Interrupted." and returns `(130, "", "")`. st needs
stdout and stderr apart (`label._run_regression` prints them to different streams), so the
two-tuple `tuple[int, str]` floated earlier is not enough; **owner decision** if sushicore wants
the two-tuple for other CLIs.

**P2. `Runner` failure codes.** `__init__(self, console, program, *, missing_exit_code: int = 1)`.
`run` and `run_drained` return `missing_exit_code` on `FileNotFoundError`. Both catch
`KeyboardInterrupt`: `run` warns "Interrupted." and returns 130; `run_drained` terminates the
child, warns, returns 130. `ConsoleLike` gains `warn(self, text: str) -> None`.

**P3. `Runner.run_drained`** passes `errors="replace"` to `Popen`.

**P4. `CMakeDriver.compile`** gains `jobs: int | None = None`; when set, argv is
`[cmake, "--build", dir, "--config", config, "--parallel", str(jobs), "--target", t, ...]`.

**P5. `CMakeDriver.ctest_run`** gains `jobs: int | None = None` and `config: str | None = None`.
Argv order: `ctest --test-dir D --output-on-failure [-L re] [-R f] [--repeat until-fail:N]
[--parallel J] [-C cfg]`. `--parallel` only when `jobs and jobs > 1`.

**P6. vcvars location and snapshot.**
`sushicore.provision.probe.find_vcvars() -> Path | None`: None off Windows; else vswhere
(`-latest -prerelease -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64
-property installationPath`), then a scan of `%ProgramFiles%` and `%ProgramFiles(x86)%` /
`Microsoft Visual Studio` / year (descending) / `BuildTools|Community|Professional|Enterprise`
/ `VC/Auxiliary/Build/vcvars64.bat`. `_resolve_windows` uses it instead of the 2022 glob.
`sushicore.build_env.snapshot_vcvars(vcvars: Path, console) -> dict[str, str] | None`: prints
`Loading Visual Studio environment from {vcvars}`, runs `cmd /c call "<vcvars>" >nul && set` as
one string, warns "vcvars64.bat returned non-zero; using the current env." and returns None on
failure, else `without_device_selection(parse_windows_set(out))`. `snapshot_windows` becomes
a wrapper that resolves `cfg.vs_vcvars` and calls it.

## Tasks

Every new or rewritten Python file opens with:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
```

st's Python files carry no license block today; this is sd's header, and the repository's
`LICENSE` is Apache-2.0. **Owner decision** whether the touched st files gain it now.

Test command for every task: `cd D:/Projects/sushitrack/cli && PYTHONPATH=D:/Projects/sushicore python -m pytest -q`.

Waves: Task 1, 2, 3 are independent (wave A). Task 4 waits on 1 and 3. Task 5 waits on 4.
Tasks 6, 7, 8 wait on 1, 2, 3 and touch disjoint files (wave C). Task 9 waits on all.

### ST-Task 1: One process runner for st

**Files:**
- Create `D:/Projects/sushitrack/cli/sushitrack_cli/process.py`
- Create `D:/Projects/sushitrack/cli/tests/test_process.py`

**Interfaces:**
- Consumes: `sushicore.proc.Runner(console, program, *, missing_exit_code)` (P1, P2, P3); `sushitrack_cli.config.PROFILE`.
- Produces: `sushitrack_cli.process.MISSING_EXIT_CODE: int = 127`; `sushitrack_cli.process.make_runner(console) -> Runner`; `sushitrack_cli.process.RUNNER: Runner`.

- [ ] Step 1: failing test. The assertions from `test_proc.py` that must survive live here, against the sushicore path.

```python
"""What st's process runner does, pinned against sushicore's Runner."""

from __future__ import annotations

import os
import sys

from conftest import RecordingConsole
from sushitrack_cli import process

MISSING = "definitely-not-a-program-4b7e"


def _runner():
    """Build a runner that records instead of printing."""
    spy = RecordingConsole()
    return process.make_runner(spy), spy


def test_run_returns_the_child_exit_code(tmp_path):
    """Returns the code the child chose."""
    runner, _ = _runner()
    assert runner.run([sys.executable, "-c", "raise SystemExit(7)"], tmp_path) == 7


def test_run_echoes_the_command(tmp_path):
    """Echoes what was run."""
    runner, spy = _runner()
    runner.run([sys.executable, "-c", "pass"], tmp_path)
    assert spy.lines


def test_a_missing_executable_keeps_st_exit_code(tmp_path):
    """Reports a missing tool with st's historic exit code 127."""
    runner, spy = _runner()
    assert runner.run([MISSING], tmp_path) == 127
    assert spy.said("Executable not found")


def test_run_drained_returns_the_child_exit_code(tmp_path):
    """Answers from the drained path the way the inherited one does."""
    runner, _ = _runner()
    assert runner.run_drained([sys.executable, "-c", "raise SystemExit(3)"], tmp_path) == 3


def test_run_drained_reports_a_missing_executable(tmp_path):
    """Says the same thing about the same failure on both run paths."""
    runner, spy = _runner()
    assert runner.run_drained([MISSING], tmp_path) == 127
    assert spy.said("Executable not found")


def test_capture_returns_the_triple_and_stays_quiet():
    """Returns code, stdout and stderr without echoing."""
    runner, spy = _runner()
    code, out, err = runner.capture([sys.executable, "-c", "print('hello')"])
    assert (code, out.strip(), err) == (0, "hello", "")
    assert spy.lines == []


def test_capture_reports_a_missing_executable_in_its_stderr():
    """Answers a missing tool in the return value."""
    runner, _ = _runner()
    code, out, err = runner.capture([MISSING])
    assert (code, out) == (127, "")
    assert "Executable not found" in err


def test_resolve_prefers_the_path_the_caller_handed_over(tmp_path):
    """Searches the env's PATH before the process's own."""
    name = "st_probe.exe" if os.name == "nt" else "st_probe"
    planted = tmp_path / name
    planted.write_text("", encoding="utf-8")
    planted.chmod(0o755)
    found = process.RUNNER.resolve_exe(planted.stem, {"PATH": str(tmp_path)})
    assert os.path.samefile(found, planted)
```

- [ ] Step 2: run; expected `ModuleNotFoundError: No module named 'sushitrack_cli.process'`.
- [ ] Step 3: implementation.

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The one sushicore Runner every st service spawns children through."""

from __future__ import annotations

from sushicore.proc import Runner

from . import console
from .config import PROFILE

#: Exit code st has always returned when a tool is missing.
MISSING_EXIT_CODE = 127


def make_runner(output) -> Runner:
    """Build a Runner that prints through *output* with st's failure codes.

    Args:
        output: A console module, or a test's recorder.

    Returns:
        A Runner named after `st`.
    """
    return Runner(output, PROFILE.program, missing_exit_code=MISSING_EXIT_CODE)


RUNNER = make_runner(console)
```

- [ ] Step 4: run; expected pass.
- [ ] Step 5: `- 2026-09-24 — cli: Added a shared sushicore process runner for st services (`cli/sushitrack_cli/process.py`).`

Acceptance: `tests/test_process.py` passes, including exit code 127 for a missing executable.

### ST-Task 2: Build-tree artifact locator

**Files:**
- Create `D:/Projects/sushitrack/cli/sushitrack_cli/services/artifacts.py`
- Create `D:/Projects/sushitrack/cli/tests/test_artifacts.py`

**Interfaces:**
- Consumes: `sushicore.discovery.ExecutableIndex(*, skip_dirs, max_depth)`; `config.IS_WINDOWS`.
- Produces: `EXECUTABLES: ExecutableIndex`; `executable_name(name: str) -> str`; `shared_lib_name() -> str`; `import_lib_name() -> str`; `find_file(build_dir, filename) -> Path | None`; `find_binary(build_dir, name) -> Path | None`. `find_artifact` is folded into `find_file` (it was an alias).

- [ ] Step 1: failing test.

```python
"""What the build-tree locator finds."""

from __future__ import annotations

from sushitrack_cli.services import artifacts


def _plant(path):
    """Create an empty executable file at *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_find_file_prefers_the_conventional_bin_dirs(tmp_path):
    """Finds bin/Release before a deeper copy."""
    name = artifacts.shared_lib_name()
    first = _plant(tmp_path / "bin" / "Release" / name)
    _plant(tmp_path / "a" / "b" / name)
    assert artifacts.find_file(tmp_path, name) == first


def test_find_file_falls_back_to_a_recursive_search(tmp_path):
    """Finds a file outside the conventional directories."""
    name = artifacts.shared_lib_name()
    deep = _plant(tmp_path / "x" / "y" / name)
    assert artifacts.find_file(tmp_path, name) == deep


def test_find_file_answers_none_without_a_build_tree(tmp_path):
    """Returns None for a missing build tree."""
    assert artifacts.find_file(tmp_path / "absent", "x") is None


def test_the_index_skips_git_and_walks_deeper_than_four(tmp_path):
    """Keeps st's unbounded-enough walk and its .git prune."""
    exe = artifacts.executable_name("deep_tool")
    deep = _plant(tmp_path / "a" / "b" / "c" / "d" / "e" / exe)
    _plant(tmp_path / ".git" / artifacts.executable_name("hook"))
    assert artifacts.EXECUTABLES.find(tmp_path) == [deep]


def test_match_prefers_an_exact_name(tmp_path):
    """Matches the exact stem before a substring."""
    exact = _plant(tmp_path / "bin" / artifacts.executable_name("unit_test"))
    _plant(tmp_path / "bin" / artifacts.executable_name("unit_test_extra"))
    assert artifacts.EXECUTABLES.match(tmp_path, "unit_test") == exact
```

- [ ] Step 2: run; expected `ImportError: cannot import name 'artifacts'`.
- [ ] Step 3: implementation.

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Locates what a SushiTrack build tree produced: libraries and executables."""

from __future__ import annotations

from pathlib import Path

from sushicore.discovery import ExecutableIndex

from ..config import IS_WINDOWS

_CONFIG_DIRS = ("", "Release", "Debug", "RelWithDebInfo")
_BIN_DIRS = ("bin", "lib", "")

#: Executables under the build tree; depth 16 stands in for st's unbounded walk.
EXECUTABLES = ExecutableIndex(skip_dirs=(".git",), max_depth=16)


def executable_name(name: str) -> str:
    """Return *name* with this platform's executable suffix."""
    return f"{name}.exe" if IS_WINDOWS else name


def shared_lib_name() -> str:
    """Return the runtime library's file name on this platform."""
    return "sushitrack.dll" if IS_WINDOWS else "libsushitrack.so"


def import_lib_name() -> str:
    """Return the library a C++ consumer links against on this platform."""
    return "sushitrack.lib" if IS_WINDOWS else "libsushitrack.so"


def _candidates(build_dir: Path, filename: str):
    """Yield the conventional locations of *filename*, most likely first."""
    for bin_dir in _BIN_DIRS:
        for config in _CONFIG_DIRS:
            yield Path(build_dir, *(p for p in (bin_dir, config, filename) if p))


def find_file(build_dir, filename: str) -> Path | None:
    """Return the path to *filename* under the build tree, or None.

    Args:
        build_dir: The build tree.
        filename: The exact file name.

    Returns:
        The first conventional hit, else the first recursive hit, else None.
    """
    build_dir = Path(build_dir)
    if not build_dir.is_dir():
        return None
    for candidate in _candidates(build_dir, filename):
        if candidate.is_file():
            return candidate
    found = sorted(build_dir.rglob(filename))
    return found[0] if found else None


def find_binary(build_dir, name: str) -> Path | None:
    """Return the built executable *name*, adding the suffix on Windows."""
    return find_file(build_dir, executable_name(name))
```

- [ ] Step 4: run; expected pass.
- [ ] Step 5: `- 2026-09-24 — cli: Added a build-tree artifact locator over sushicore's ExecutableIndex (`cli/sushitrack_cli/services/artifacts.py`).`

Acceptance: `tests/test_artifacts.py` passes, including a binary five levels deep.

### ST-Task 3: Build environment on sushicore.build_env

**Files:**
- Modify (rewrite) `D:/Projects/sushitrack/cli/sushitrack_cli/env.py`
- Modify (rewrite) `D:/Projects/sushitrack/cli/tests/test_env.py`

**Interfaces:**
- Consumes: `sushicore.build_env.read_cache(path, key)`, `write_cache(path, key, env)`, `merge_env(base, overlay)`, `snapshot_vcvars(path, console)` (P6); `sushicore.provision.probe.find_vcvars()` (P6); `cfg.tool.platform`, `.vs_vcvars`, `.expand`, `.is_windows`.
- Produces: `CACHE_NAME = ".sushitrack_env.json"`; `cache_key(tool) -> str`; `vcvars_path(tool) -> Path | None`; `load_build_env(tool, build_dir) -> dict[str, str]`. Old `load_build_env(build_dir)`, `find_vcvars`, `_merge`, `_snapshot_windows` are gone.

Tests: the four `_merge` tests are deleted; `merge_env` is sushicore's and tested there. The cache and snapshot tests survive below against the new function. `test_a_cache_is_reused_whatever_produced_it` is inverted, as its own docstring predicted.

Callers of the old signature (`build.py`, `tests.py`, `runner.py`, `label.py`, `diag.py`) break until Tasks 4 to 8 land. Run Task 3 in the same wave as its callers, or accept a red suite between waves.

- [ ] Step 1: failing test.

```python
"""What st's build environment does, now composed from sushicore.build_env."""

from __future__ import annotations

import json
import os
from types import SimpleNamespace

from sushitrack_cli import env


def _tool(windows=True, vcvars="C:/vs/vcvars64.bat"):
    """Build the slice of ToolSettings env.py reads."""
    return SimpleNamespace(platform="windows" if windows else "linux",
                           vs_vcvars=vcvars, is_windows=windows,
                           expand=lambda value: value)


def _no_vcvars_run(monkeypatch):
    """Fail the test if a vcvars snapshot is attempted."""
    monkeypatch.setattr(env, "snapshot_vcvars",
                        lambda *a: (_ for _ in ()).throw(AssertionError("vcvars ran")))


def test_off_windows_the_current_environment_is_used_as_is(tmp_path, monkeypatch):
    """Snapshots nothing off Windows."""
    _no_vcvars_run(monkeypatch)
    assert env.load_build_env(_tool(windows=False), tmp_path) == dict(os.environ)


def test_a_cached_snapshot_is_read_back(tmp_path, monkeypatch):
    """Runs vcvars once per build tree."""
    _no_vcvars_run(monkeypatch)
    tool = _tool()
    (tmp_path / env.CACHE_NAME).write_text(json.dumps(
        {"key": env.cache_key(tool), "env": {"INCLUDE": "C:/from-cache"}}), encoding="utf-8")
    assert env.load_build_env(tool, tmp_path)["INCLUDE"] == "C:/from-cache"


def test_a_cache_from_another_vcvars_is_ignored(tmp_path, monkeypatch):
    """Rejects a snapshot whose key no longer matches."""
    monkeypatch.delenv("VSINSTALLDIR", raising=False)
    monkeypatch.setattr(env, "snapshot_vcvars", lambda path, out: {"INCLUDE": "C:/fresh"})
    (tmp_path / env.CACHE_NAME).write_text(json.dumps(
        {"key": "stale", "env": {"INCLUDE": "C:/gone"}}), encoding="utf-8")
    assert env.load_build_env(_tool(), tmp_path)["INCLUDE"] == "C:/fresh"


def test_an_unreadable_cache_is_rebuilt_rather_than_fatal(tmp_path, monkeypatch):
    """Costs a vcvars run, not the build."""
    monkeypatch.delenv("VSINSTALLDIR", raising=False)
    monkeypatch.setattr(env, "snapshot_vcvars", lambda path, out: {"INCLUDE": "C:/fresh"})
    (tmp_path / env.CACHE_NAME).write_text("{ not json", encoding="utf-8")
    assert env.load_build_env(_tool(), tmp_path)["INCLUDE"] == "C:/fresh"


def test_a_fresh_snapshot_is_written_to_the_cache(tmp_path, monkeypatch):
    """Keeps what was learned under the current key."""
    monkeypatch.delenv("VSINSTALLDIR", raising=False)
    monkeypatch.setattr(env, "snapshot_vcvars", lambda path, out: {"LIB": "C:/libs"})
    tool = _tool()
    env.load_build_env(tool, tmp_path)
    cached = json.loads((tmp_path / env.CACHE_NAME).read_text(encoding="utf-8"))
    assert cached == {"key": env.cache_key(tool), "env": {"LIB": "C:/libs"}}


def test_no_snapshot_means_the_environment_is_left_alone(tmp_path, monkeypatch):
    """Changes nothing when vcvars fails."""
    monkeypatch.delenv("VSINSTALLDIR", raising=False)
    monkeypatch.setattr(env, "snapshot_vcvars", lambda path, out: None)
    assert env.load_build_env(_tool(), tmp_path) == dict(os.environ)
    assert not (tmp_path / env.CACHE_NAME).exists()


def test_a_developer_shell_is_not_snapshotted_again(tmp_path, monkeypatch):
    """Skips vcvars inside a VS developer shell."""
    monkeypatch.setenv("VSINSTALLDIR", "C:/vs")
    _no_vcvars_run(monkeypatch)
    assert env.load_build_env(_tool(), tmp_path) == dict(os.environ)


def test_no_visual_studio_warns_and_uses_the_current_env(tmp_path, monkeypatch, recorder):
    """Warns once and carries on when no vcvars exists."""
    spy = recorder(env)
    monkeypatch.delenv("VSINSTALLDIR", raising=False)
    monkeypatch.setattr(env, "find_vcvars", lambda: None)
    _no_vcvars_run(monkeypatch)
    assert env.load_build_env(_tool(vcvars=""), tmp_path) == dict(os.environ)
    assert spy.said("No Visual Studio installation detected")


def test_a_configured_vcvars_wins_over_detection(monkeypatch, tmp_path):
    """Prefers cfg.tool.vs_vcvars when it names a file."""
    bat = tmp_path / "vcvars64.bat"
    bat.write_text("", encoding="utf-8")
    monkeypatch.setattr(env, "find_vcvars", lambda: tmp_path / "other.bat")
    assert env.vcvars_path(_tool(vcvars=str(bat))) == bat
```

- [ ] Step 2: run; expected `AttributeError: module 'sushitrack_cli.env' has no attribute 'cache_key'`.
- [ ] Step 3: implementation.

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Assembles the environment st's build, test and run children see."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from sushicore.build_env import merge_env, read_cache, snapshot_vcvars, write_cache
from sushicore.provision.probe import find_vcvars

from . import console

CACHE_NAME = ".sushitrack_env.json"


def cache_key(tool) -> str:
    """Hash the settings that decide what a vcvars snapshot contains."""
    material = json.dumps({"platform": tool.platform, "vs_vcvars": tool.vs_vcvars},
                          sort_keys=True)
    return hashlib.sha256(material.encode()).hexdigest()


def vcvars_path(tool) -> Path | None:
    """Return the configured vcvars64.bat when it exists, else the detected one."""
    configured = tool.expand(tool.vs_vcvars) if tool.vs_vcvars else ""
    if configured and Path(configured).is_file():
        return Path(configured)
    return find_vcvars()


def _snapshot(tool) -> dict[str, str] | None:
    """Return a fresh vcvars snapshot, or None when there is nothing to take."""
    if os.environ.get("VSINSTALLDIR"):
        return None
    vcvars = vcvars_path(tool)
    if vcvars is None:
        console.warn("No Visual Studio installation detected; "
                     "assuming the compiler is already on PATH.")
        return None
    return snapshot_vcvars(vcvars, console)


def load_build_env(tool, build_dir) -> dict[str, str]:
    """Return the environment for build, test and run children.

    Args:
        tool: The resolved `cfg.tool` settings.
        build_dir: Where the snapshot cache lives.

    Returns:
        `os.environ` off Windows or without a snapshot; else it merged with one.
    """
    if not tool.is_windows:
        return dict(os.environ)
    cache_file = Path(build_dir) / CACHE_NAME
    key = cache_key(tool)
    snapshot = read_cache(cache_file, key)
    if snapshot is None:
        snapshot = _snapshot(tool)
        if not snapshot:
            return dict(os.environ)
        try:
            Path(build_dir).mkdir(parents=True, exist_ok=True)
        except OSError:
            return merge_env(os.environ, snapshot)
        write_cache(cache_file, key, snapshot)
    return merge_env(os.environ, snapshot)
```

- [ ] Step 4: run `tests/test_env.py`; expected pass. The full suite is green after Task 8.
- [ ] Step 5: `- 2026-09-24 — cli: Rebuilt the vcvars build environment on sushicore.build_env with a keyed cache (`cli/sushitrack_cli/env.py`).`

Acceptance: `tests/test_env.py` passes and a cache written under another key is ignored.

### ST-Task 4: st build on CMakeDriver

**Files:**
- Modify `D:/Projects/sushitrack/cli/sushitrack_cli/services/build.py`
- Create `D:/Projects/sushitrack/cli/tests/test_build_service.py`

**Interfaces:**
- Consumes: `CMakeDriver(console, runner)`, `.cmake(tool)`, `.needs_configure(dir, gen, root=)`, `.configure(args, cwd, env)`, `.compile(tool, dir, cwd, env, config=, targets=, jobs=)` (P4); `cmake_cache.cached_value`, `is_stale`; `process.RUNNER`; `env.load_build_env(tool, dir)`.
- Produces: `DRIVER: CMakeDriver`; `generator(cfg) -> str`; `build(cfg, paths, build_type=None, clean=False, jobs=None, tests=True, defines=()) -> int` (unchanged signature). Removed: `cmake_exe`, `cache_value`, `stale_tree`. Kept: `BuildType`, `BUILD_TYPES`, `normalize_build_type`, `clean`, `LIBRARY_TARGET`, `TEST_TARGETS`, `TEST_OPTIONS`, `STAMP_NAME`.

- [ ] Step 1: failing test.

```python
"""What `st build` hands cmake, pinned through a recording runner."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from sushicore.cmake_driver import CMakeDriver

from conftest import RecordingConsole
from sushitrack_cli.services import build as build_svc


class RecordingRunner:
    """Record argv instead of running it."""

    def __init__(self):
        self.calls = []

    def run(self, cmd, cwd, env=None):
        """Record *cmd* and succeed."""
        self.calls.append(list(cmd))
        return 0


def _cfg(generator="", windows=True):
    """Build a Config slice with st's tool settings."""
    tool = SimpleNamespace(cmake_exe="", ctest_exe="", generator=generator,
                           is_windows=windows, platform="x", vs_vcvars="",
                           expand=lambda v: v)
    return SimpleNamespace(tool=tool, build_type="Release", jobs=lambda: 4)


@pytest.fixture
def runner(monkeypatch, recorder):
    """Swap in a recording runner and a quiet environment."""
    recorder(build_svc)
    rec = RecordingRunner()
    monkeypatch.setattr(build_svc, "DRIVER", CMakeDriver(RecordingConsole(), rec))
    monkeypatch.setattr(build_svc, "load_build_env", lambda tool, d: {})
    return rec


@pytest.mark.parametrize("windows, expected", [(True, "Ninja"), (False, "")])
def test_the_default_generator_follows_the_host(windows, expected):
    """Defaults to Ninja on Windows and CMake's choice elsewhere."""
    assert build_svc.generator(_cfg(windows=windows)) == expected


def test_a_configured_generator_wins():
    """Uses the generator the config names."""
    assert build_svc.generator(_cfg(generator="Unix Makefiles")) == "Unix Makefiles"


def test_a_fresh_tree_is_configured_then_built(tmp_path, runner):
    """Emits the same configure and build argv st always has."""
    paths = SimpleNamespace(root=tmp_path, build=tmp_path / "build")
    assert build_svc.build(_cfg(), paths, build_type="Debug", jobs=3) == 0
    configure, compile_ = runner.calls
    assert configure == ["cmake", "-S", str(tmp_path), "-B", str(paths.build),
                         "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Debug", "-DBUILD_MOT_TEST=OFF",
                         "-DBUILD_UNIT_TEST=ON", "-DBUILD_REGRESSION_TEST=ON",
                         "-DBUILD_INTEGRATION_TEST=ON"]
    assert compile_ == ["cmake", "--build", str(paths.build), "--config", "Debug",
                        "--parallel", "3", "--target", "sushitrack",
                        "--target", "unit_test", "--target", "integration_test",
                        "--target", "regression_test", "--target", "tracker_bridge"]


def test_a_matching_stamp_skips_configure(tmp_path, runner):
    """Builds without reconfiguring when the stamp matches."""
    build = tmp_path / "build"
    build.mkdir()
    (build / "build.ninja").write_text("", encoding="utf-8")
    (build / "CMakeCache.txt").write_text(
        f"CMAKE_HOME_DIRECTORY:INTERNAL={tmp_path}\n", encoding="utf-8")
    (build / build_svc.STAMP_NAME).write_text("Release|OFF|Ninja", encoding="utf-8")
    paths = SimpleNamespace(root=tmp_path, build=build)
    assert build_svc.build(_cfg(), paths, tests=False) == 0
    assert [c[1] for c in runner.calls] == ["--build"]


def test_a_visual_studio_tree_is_not_reconfigured_for_a_missing_makefile(tmp_path, runner):
    """Needs no sentinel file for a multi-config generator."""
    build = tmp_path / "build"
    build.mkdir()
    (build / "CMakeCache.txt").write_text(
        f"CMAKE_HOME_DIRECTORY:INTERNAL={tmp_path}\n", encoding="utf-8")
    gen = "Visual Studio 17 2022"
    (build / build_svc.STAMP_NAME).write_text(f"Release|OFF|{gen}", encoding="utf-8")
    paths = SimpleNamespace(root=tmp_path, build=build)
    assert build_svc.build(_cfg(generator=gen), paths, tests=False) == 0
    assert len(runner.calls) == 1
```

- [ ] Step 2: run; expected `AttributeError: ... has no attribute 'DRIVER'`.
- [ ] Step 3: implementation. Replace the module's imports and everything from `cmake_exe` through `build`; leave `BuildType`, the constants, `normalize_build_type` and `clean` as they are.

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Configure, build and clean the project."""

import enum
import shutil
from pathlib import Path

from sushicore import cmake_cache
from sushicore.cmake_driver import CMakeDriver

from .. import console
from ..env import load_build_env
from ..process import RUNNER

# ... BUILD_TYPES, BuildType, LIBRARY_TARGET, TEST_TARGETS, TEST_OPTIONS,
# STAMP_NAME, normalize_build_type: unchanged ...

#: Generators whose configured tree leaves a build file behind.
_SENTINEL_GENERATORS = ("Ninja", "Unix Makefiles", "")

DRIVER = CMakeDriver(console, RUNNER)


def generator(cfg) -> str:
    """Return the configured generator, else Ninja on Windows and CMake's default elsewhere."""
    configured = cfg.tool.expand(cfg.tool.generator)
    if configured:
        return configured
    return "Ninja" if cfg.tool.is_windows else ""


def _stamp_key(build_type, tests, generator_name, defines):
    """Join the settings that force a reconfigure when they change."""
    return "|".join([build_type, "ON" if tests else "OFF", generator_name,
                     *sorted(defines)])


def _needs_configure(build_dir: Path, generator_name: str, stamp_key: str,
                     root: Path) -> bool:
    """Return whether the tree must be configured from scratch."""
    if generator_name in _SENTINEL_GENERATORS:
        if DRIVER.needs_configure(build_dir, generator_name, root=root):
            return True
    elif not build_dir.is_dir():
        return True
    elif cmake_cache.is_stale(build_dir, root):
        console.warn("Build tree was configured for a different source path "
                     "(e.g. a Docker volume build); reconfiguring from scratch.")
        return True
    if not (build_dir / "CMakeCache.txt").is_file():
        return True
    stamp = build_dir / STAMP_NAME
    if not stamp.is_file():
        return True
    return stamp.read_text(encoding="utf-8").strip() != stamp_key


def _configure_args(cfg, paths, build_type, tests, generator_name, defines):
    """Return the configure argv st's build policy asks for."""
    args = [DRIVER.cmake(cfg.tool), "-S", str(paths.root), "-B", str(paths.build)]
    if generator_name:
        args += ["-G", generator_name]
    args += [f"-DCMAKE_BUILD_TYPE={build_type}", "-DBUILD_MOT_TEST=OFF"]
    args += [f"-D{option}={'ON' if tests else 'OFF'}" for option in TEST_OPTIONS]
    return args + list(defines)


def build(cfg, paths, build_type=None, clean=False, jobs=None, tests=True,
          defines=()):
    """Configure when needed, then build st's targets.

    Returns:
        The exit code of the failing step, else 0.
    """
    console.header("Build")
    build_dir = paths.build
    build_type = build_type or normalize_build_type(cfg.build_type)
    generator_name = generator(cfg)

    if clean and build_dir.exists():
        console.info(f"Removing build directory: {build_dir}")
        shutil.rmtree(build_dir, ignore_errors=True)

    console.info(f"Type: {build_type}  |  tests: {'ON' if tests else 'OFF'}"
                 + (f"  |  generator: {generator_name}" if generator_name else ""))

    env = load_build_env(cfg.tool, build_dir)
    stamp_key = _stamp_key(build_type, tests, generator_name, defines)

    if _needs_configure(build_dir, generator_name, stamp_key, paths.root):
        if build_dir.exists():
            shutil.rmtree(build_dir, ignore_errors=True)
        build_dir.mkdir(parents=True, exist_ok=True)
        console.info("Configuring...")
        args = _configure_args(cfg, paths, build_type, tests, generator_name, defines)
        code = DRIVER.configure(args, paths.root, env)
        if code != 0:
            console.error("CMake configuration failed.")
            return code
        (build_dir / STAMP_NAME).write_text(stamp_key, encoding="utf-8")
    else:
        console.info("Build tree already configured for this configuration; "
                     "skipping cmake configure.")

    targets = [LIBRARY_TARGET] + (list(TEST_TARGETS) if tests else [])
    console.info("Building...")
    code = DRIVER.compile(cfg.tool, build_dir, paths.root, env, config=build_type,
                          targets=targets, jobs=jobs or cfg.jobs())
    if code != 0:
        console.error("Build failed.")
        return code
    console.success(f"Build completed ({', '.join(targets)}).")
    return 0
```

Note for the implementer: the stale-tree warning must print once. `DRIVER.needs_configure` prints it for sentinel generators; the `elif` branch prints it for the rest. `diag.py` and `tests.py` still reference `build_svc.cache_value`/`stale_tree` until Tasks 5 and 8.

- [ ] Step 4: run `tests/test_build_service.py`; expected pass.
- [ ] Step 5: `- 2026-09-24 — cli: Moved st build's cmake configure and compile onto sushicore's CMakeDriver (`cli/sushitrack_cli/services/build.py`).`

Acceptance: the configure and build argv in `test_a_fresh_tree_is_configured_then_built` match st's pre-migration argv exactly.

### ST-Task 5: st test on CMakeDriver.ctest_run

**Files:**
- Modify `D:/Projects/sushitrack/cli/sushitrack_cli/services/tests.py`
- Create `D:/Projects/sushitrack/cli/tests/test_test_service.py`

**Interfaces:**
- Consumes: `build.DRIVER`; `CMakeDriver.ctest_run(tool, dir, env, label_regex=, filter=, repeat=, jobs=, config=)` (P5); `cmake_cache.cached_value`, `is_stale`; `env.load_build_env(tool, dir)`.
- Produces: `test(cfg, paths, suite=DEFAULT_SUITE, filter=None, repeat=0, jobs=None) -> int` (unchanged). Removed: `ctest_exe`. `SUITE_LABELS`, `SUITES`, `DEFAULT_SUITE`, `Suite` unchanged.

- [ ] Step 1: failing test.

```python
"""What `st test` hands ctest."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from sushicore.cmake_driver import CMakeDriver

from conftest import RecordingConsole
from sushitrack_cli.services import build as build_svc
from sushitrack_cli.services import tests as test_svc


class DrainRecorder:
    """Record drained argv instead of running it."""

    def __init__(self):
        self.calls = []

    def run_drained(self, cmd, cwd, env=None):
        """Record *cmd* and succeed."""
        self.calls.append(list(cmd))
        return 0


def _tree(tmp_path, cache):
    """Create a configured tree whose cache holds *cache*."""
    build = tmp_path / "build"
    build.mkdir()
    (build / "CMakeCache.txt").write_text(
        f"CMAKE_HOME_DIRECTORY:INTERNAL={tmp_path}\n{cache}", encoding="utf-8")
    return SimpleNamespace(root=tmp_path, build=build)


@pytest.fixture
def rec(monkeypatch, recorder):
    """Swap in a recording runner."""
    recorder(test_svc)
    runner = DrainRecorder()
    monkeypatch.setattr(build_svc, "DRIVER", CMakeDriver(RecordingConsole(), runner))
    monkeypatch.setattr(test_svc, "load_build_env", lambda tool, d: {})
    return runner


_CFG = SimpleNamespace(build_type="Release",
                       tool=SimpleNamespace(ctest_exe="", expand=lambda v: v))


def test_single_config_tree_passes_no_config_flag(tmp_path, rec):
    """Emits st's argv for the functional suite."""
    paths = _tree(tmp_path, "CMAKE_BUILD_TYPE:STRING=Release\n")
    assert test_svc.test(_CFG, paths, suite="functional", jobs=2) == 0
    assert rec.calls == [["ctest", "--test-dir", str(paths.build), "--output-on-failure",
                          "-L", "^(unit|integration|regression)$", "--parallel", "2"]]


def test_multi_config_tree_gets_a_config(tmp_path, rec):
    """Adds -C when the cache carries no build type."""
    paths = _tree(tmp_path, "")
    test_svc.test(_CFG, paths, suite="all", filter="A.B", repeat=3)
    assert rec.calls[0][-2:] == ["-C", "Release"]
    assert "-L" not in rec.calls[0]
    assert rec.calls[0][4:8] == ["-R", "A.B", "--repeat", "until-fail:3"]


def test_a_stale_tree_is_refused(tmp_path, rec):
    """Refuses a tree configured for another source path."""
    build = tmp_path / "build"
    build.mkdir()
    (build / "CMakeCache.txt").write_text(
        "CMAKE_HOME_DIRECTORY:INTERNAL=/workspace\n", encoding="utf-8")
    paths = SimpleNamespace(root=tmp_path, build=build)
    assert test_svc.test(_CFG, paths) == 1
    assert rec.calls == []
```

- [ ] Step 2: run; expected failure on `load_build_env` signature or missing `--parallel` from the driver.
- [ ] Step 3: implementation. Replace imports, delete `ctest_exe`, replace `test`.

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Test execution through CTest labels."""

import enum

from sushicore import cmake_cache

from .. import console
from ..env import load_build_env
from . import build as build_svc

# ... SUITE_LABELS, SUITES, DEFAULT_SUITE, Suite: unchanged ...


def _config_flag(cfg, build_dir):
    """Return the -C value a multi-config tree needs, or None for a single-config one."""
    if cmake_cache.cached_value(build_dir, "CMAKE_BUILD_TYPE"):
        return None
    return build_svc.normalize_build_type(cfg.build_type)


def test(cfg, paths, suite=DEFAULT_SUITE, filter=None, repeat=0, jobs=None):
    """Run a suite via CTest.

    Returns:
        ctest's exit code, or 1 when the tree is absent or stale.
    """
    console.header("Test")
    build_dir = paths.build
    if not build_dir.is_dir():
        console.error(f"{build_dir} not found. Run `st build` first.")
        return 1
    if cmake_cache.is_stale(build_dir, paths.root):
        console.error(
            f"{build_dir} was configured for a different source path "
            f"(e.g. a Docker volume build reused on this host).\n"
            f"  - run `st build --clean` to reconfigure it cleanly first.")
        return 1

    console.info(f"Suite: {suite}")
    code = build_svc.DRIVER.ctest_run(
        cfg.tool, build_dir, load_build_env(cfg.tool, build_dir),
        label_regex=None if suite == "all" else SUITE_LABELS[suite],
        filter=filter, repeat=repeat, jobs=jobs,
        config=_config_flag(cfg, build_dir))
    if code != 0:
        console.error(f"Suite '{suite}' failed (exit {code}).")
    return code
```

"Suite: ..." now prints before the ctest echo and the repeat notice, where it printed after both. **Owner decision** only if that ordering matters; otherwise accepted.

- [ ] Step 4: run `tests/test_test_service.py`; expected pass.
- [ ] Step 5: `- 2026-09-24 — cli: Moved st test's ctest invocation onto sushicore's CMakeDriver.ctest_run (`cli/sushitrack_cli/services/tests.py`).`

Acceptance: ctest argv for `functional`, `all` with filter and repeat, and a multi-config tree matches st's pre-migration argv.

### ST-Task 6: run, label and deploy onto the new bricks

**Files:**
- Modify `D:/Projects/sushitrack/cli/sushitrack_cli/services/runner.py`
- Modify `D:/Projects/sushitrack/cli/sushitrack_cli/services/label.py`
- Modify `D:/Projects/sushitrack/cli/sushitrack_cli/services/deploy.py`
- Create `D:/Projects/sushitrack/cli/tests/test_run_label_deploy.py`

**Interfaces:**
- Consumes: `process.RUNNER.run/.capture`; `artifacts.EXECUTABLES`, `find_file`, `find_binary`, `shared_lib_name`, `import_lib_name`; `env.load_build_env(tool, dir)`.
- Produces: `label._run_regression(cfg, paths, gtest_filter) -> tuple[int, dict]` (gains `cfg`); other public signatures unchanged.

- [ ] Step 1: failing test.

```python
"""run, label and deploy reach the build tree through artifacts and process."""

from __future__ import annotations

import sys
from types import SimpleNamespace

from sushitrack_cli.services import deploy, label, runner


def test_run_matches_through_the_shared_index(tmp_path, monkeypatch, recorder):
    """Runs the matched binary with the build env."""
    recorder(runner)
    seen = {}
    monkeypatch.setattr(runner.EXECUTABLES, "match", lambda build, q: tmp_path / "t.exe")
    monkeypatch.setattr(runner, "load_build_env", lambda tool, d: {"X": "1"})
    monkeypatch.setattr(runner.RUNNER, "run",
                        lambda cmd, cwd, env=None: seen.update(cmd=cmd, env=env) or 0)
    cfg = SimpleNamespace(tool=SimpleNamespace())
    paths = SimpleNamespace(root=tmp_path, build=tmp_path)
    assert runner.run(cfg, paths, target="t", forwarded=("--a",)) == 0
    assert seen == {"cmd": [str(tmp_path / "t.exe"), "--a"], "env": {"X": "1"}}


def test_regression_capture_keeps_streams_apart(tmp_path, monkeypatch, recorder):
    """Parses PERF lines from stdout of a captured run."""
    recorder(label)
    monkeypatch.setattr(label, "find_binary", lambda build, name: sys.executable)
    monkeypatch.setattr(label, "load_build_env", lambda tool, d: None)
    monkeypatch.setattr(label.RUNNER, "capture", lambda cmd, cwd=None, env=None: (0, "", ""))
    cfg = SimpleNamespace(tool=SimpleNamespace())
    paths = SimpleNamespace(root=tmp_path, build=tmp_path)
    assert label._run_regression(cfg, paths, "*") == (0, {})


def test_deploy_no_longer_imports_discovery():
    """Uses the artifact locator."""
    assert not hasattr(deploy, "discovery")
    assert deploy.shared_lib_name() in ("sushitrack.dll", "libsushitrack.so")
```

- [ ] Step 2: run; expected `AttributeError: ... has no attribute 'EXECUTABLES'`.
- [ ] Step 3: implementation.

`runner.py`: imports become

```python
from .. import console
from ..env import load_build_env
from ..process import RUNNER
from .artifacts import EXECUTABLES
```

`_select`: `executables = EXECUTABLES.find(paths.build)`; the table, `input()` and error text stay. `run`: `binary = EXECUTABLES.match(paths.build, target)`; the launch becomes

```python
    console.header(f"Run {binary.name}")
    return RUNNER.run([str(binary), *forwarded], paths.root,
                      env=load_build_env(cfg.tool, paths.build))
```

`label.py`: imports become `from .. import console`, `from ..env import load_build_env`, `from ..process import RUNNER`, `from . import evaluate`, `from .artifacts import find_binary`. Replace `_run_regression` and its one call site (`_run_regression(cfg, paths, _gtest_filter(names, trackers))`):

```python
def _run_regression(cfg, paths, gtest_filter):
    """Run regression_test under *gtest_filter* and parse its PERF lines.

    Returns:
        The exit code and, on success, tracker to sequence to microseconds per frame.
    """
    binary = find_binary(paths.build, "regression_test")
    if not binary:
        console.error("regression_test binary not found. Run `st build` first.")
        return 1, {}

    console.command(f"{binary} --gtest_filter={gtest_filter}")
    code, out, err = RUNNER.capture([str(binary), f"--gtest_filter={gtest_filter}"],
                                    cwd=paths.root,
                                    env=load_build_env(cfg.tool, paths.build))
    if code != 0:
        console.error(f"regression_test failed (exit {code}).")
        print(out)
        print(err, file=sys.stderr)
        return code, {}
    return 0, _parse_perf(out)
```

`deploy.py`: `from . import discovery` becomes `from .artifacts import find_file, import_lib_name, shared_lib_name`; every `discovery.find_artifact(` becomes `find_file(`, every `discovery.shared_lib_name()` becomes `shared_lib_name()`, every `discovery.import_lib_name()` becomes `import_lib_name()` (lines 176 to 234 today).

- [ ] Step 4: run; expected pass.
- [ ] Step 5: `- 2026-09-24 — cli: Moved st run, label and deploy onto the shared runner and artifact locator (`services/runner.py`, `services/label.py`, `services/deploy.py`).`

Acceptance: `grep -n "discovery\|proc\." runner.py label.py deploy.py` prints nothing and the new tests pass.

### ST-Task 7: docker, infer and eval onto the shared runner

**Files:**
- Modify `D:/Projects/sushitrack/cli/sushitrack_cli/services/docker.py`
- Modify `D:/Projects/sushitrack/cli/sushitrack_cli/services/infer.py`
- Modify `D:/Projects/sushitrack/cli/sushitrack_cli/services/evaluate.py`
- Create `D:/Projects/sushitrack/cli/tests/test_plain_runs.py`

**Interfaces:**
- Consumes: `process.RUNNER.run(cmd, cwd, env=None)`.
- Produces: nothing new; public signatures unchanged.

- [ ] Step 1: failing test.

```python
"""docker, infer and eval spawn through the shared runner."""

from __future__ import annotations

import importlib

import pytest


@pytest.mark.parametrize("name", ["docker", "infer", "evaluate"])
def test_the_service_uses_the_shared_runner(name):
    """Holds RUNNER, not the old proc module."""
    module = importlib.import_module(f"sushitrack_cli.services.{name}")
    assert not hasattr(module, "proc")
    assert module.RUNNER is importlib.import_module("sushitrack_cli.process").RUNNER
```

- [ ] Step 2: run; expected `AssertionError` on `hasattr(module, "proc")`.
- [ ] Step 3: implementation. In each file, `from .. import console, proc` becomes `from .. import console` plus `from ..process import RUNNER`. Then:
  - `docker.py:18` `code = RUNNER.run(command, paths.root)`; `docker.py:39` `return RUNNER.run(argv, paths.root)`.
  - `infer.py:59` `return RUNNER.run(command, paths.root)`.
  - `evaluate.py:150` `if RUNNER.run(command, trackeval_dir) != 0:`.

  Each `command` is already a list, which `Runner.run` requires. `infer.py` and `evaluate.py` pass `sys.executable` as argv[0]; `resolve_exe` keeps an absolute path unchanged.
- [ ] Step 4: run; expected pass.
- [ ] Step 5: `- 2026-09-24 — cli: Moved st docker, infer and eval onto the shared sushicore runner (`services/docker.py`, `services/infer.py`, `services/evaluate.py`).`

Acceptance: the parametrized test passes for all three services.

### ST-Task 8: diag's status, paths and env onto the new bricks

`diag.doctor` is out of scope. If the doctor replacement has not landed, leave `doctor` and the imports only it uses (`proc`, `find_vcvars`, `test_svc`) in place; Task 9 then waits.

**Files:**
- Modify `D:/Projects/sushitrack/cli/sushitrack_cli/services/diag.py`
- Create `D:/Projects/sushitrack/cli/tests/test_diag_service.py`

**Interfaces:**
- Consumes: `process.RUNNER.capture`; `artifacts.find_file`, `find_binary`, `shared_lib_name`; `cmake_cache.cached_value`; `env.load_build_env(tool, dir)`.
- Produces: `_git_describe(paths) -> str | None` (same contract); `status`, `env_dump` signatures unchanged.

- [ ] Step 1: failing test.

```python
"""diag's git probe and env dump on the shared bricks."""

from __future__ import annotations

from types import SimpleNamespace

from sushitrack_cli.services import diag


def test_git_missing_answers_none(tmp_path, monkeypatch):
    """Returns None when git cannot be spawned."""
    monkeypatch.setattr(diag.RUNNER, "capture", lambda cmd, cwd=None, env=None: (127, "", ""))
    assert diag._git_describe(SimpleNamespace(root=tmp_path)) is None


def test_git_describe_joins_branch_commit_and_dirt(tmp_path, monkeypatch):
    """Reads branch, commit and porcelain status."""
    answers = iter([(0, "main\n", ""), (0, "abc123\n", ""), (0, " M x\n", "")])
    monkeypatch.setattr(diag.RUNNER, "capture", lambda cmd, cwd=None, env=None: next(answers))
    assert diag._git_describe(SimpleNamespace(root=tmp_path)) == "main @ abc123 (dirty)"


def test_env_dump_reads_the_tool_settings(tmp_path, monkeypatch, recorder):
    """Loads the build env from cfg.tool."""
    recorder(diag)
    seen = {}
    monkeypatch.setattr(diag, "load_build_env",
                        lambda tool, d: seen.setdefault("tool", tool) and {"PATH": "x"})
    tool = SimpleNamespace(name="tool")
    assert diag.env_dump(SimpleNamespace(tool=tool), SimpleNamespace(build=tmp_path)) == 0
    assert seen["tool"] is tool
```

- [ ] Step 2: run; expected `AttributeError: ... has no attribute 'RUNNER'`.
- [ ] Step 3: implementation. Imports: add `from sushicore import cmake_cache`, `from ..process import RUNNER`, `from .artifacts import find_binary, find_file, shared_lib_name`; drop `from . import discovery`. Then:

```python
def _git_describe(paths):
    """Return "branch @ commit" with a dirty marker, or None without git."""
    code, out, _ = RUNNER.capture(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                  cwd=paths.root)
    if code == 127:
        return None
    branch = out.strip() if code == 0 else "?"
    code, out, _ = RUNNER.capture(["git", "rev-parse", "--short", "HEAD"], cwd=paths.root)
    commit = out.strip() if code == 0 else "?"
    code, out, _ = RUNNER.capture(["git", "status", "--porcelain"], cwd=paths.root)
    dirty = " (dirty)" if code == 0 and out.strip() else ""
    return f"{branch} @ {commit}{dirty}"
```

In `status`: `build_svc.cache_value(` becomes `cmake_cache.cached_value(`; `discovery.find_artifact(` becomes `find_file(`; `discovery.find_binary(` becomes `find_binary(`; `discovery.shared_lib_name()` becomes `shared_lib_name()`. In `env_dump`: `env = load_build_env(cfg.tool, paths.build)`.

`_git_describe` no longer asks `which` first; a missing git now costs one failed spawn instead of a PATH lookup. Output is unchanged.
- [ ] Step 4: run; expected pass. The full suite is green from here.
- [ ] Step 5: `- 2026-09-24 — cli: Moved st status and st env onto the shared runner, artifact locator and cmake cache reader (`services/diag.py`).`

Acceptance: the full suite passes and `diag.py` outside `doctor` references neither `proc` nor `discovery`.

### ST-Task 9: Delete st's copies

Waits on Tasks 1 to 8 and on the doctor replacement.

**Files:**
- Delete `D:/Projects/sushitrack/cli/sushitrack_cli/proc.py`
- Delete `D:/Projects/sushitrack/cli/sushitrack_cli/services/discovery.py`
- Delete `D:/Projects/sushitrack/cli/tests/test_proc.py` (its surviving assertions moved to `test_process.py` in Task 1; `format_command` and `tool_version` tests are dropped with the functions)
- Create `D:/Projects/sushitrack/cli/tests/test_no_local_copies.py`
- Modify `D:/Projects/sushitrack/docs/architecture/OVERVIEW.md` and `D:/Projects/sushitrack/cli/README.md` wherever they name `proc.py`, `discovery.py`, `build_cmake`, `build_ctest` or `find_vcvars` (grep before editing; the implementer lists each hit in the report)

**Interfaces:**
- Consumes: nothing.
- Produces: nothing; removes `sushitrack_cli.proc` and `sushitrack_cli.services.discovery`.

- [ ] Step 1: failing test.

```python
"""st carries no copy of machinery sushicore owns."""

from __future__ import annotations

import importlib.util
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "sushitrack_cli"


def test_the_copies_are_gone():
    """Removes proc and discovery."""
    assert importlib.util.find_spec("sushitrack_cli.proc") is None
    assert importlib.util.find_spec("sushitrack_cli.services.discovery") is None


def test_nothing_imports_them():
    """Leaves no import of the removed modules."""
    offenders = [p.name for p in PACKAGE.rglob("*.py")
                 if "import proc" in (text := p.read_text(encoding="utf-8"))
                 or ", proc" in text or "import discovery" in text]
    assert offenders == []
```

- [ ] Step 2: run; expected `test_the_copies_are_gone` fails.
- [ ] Step 3: `git rm` the three files (the implementer runs it; this plan does not), then fix the doc hits.
- [ ] Step 4: run; expected pass.
- [ ] Step 5: `- 2026-09-24 — cli: Removed st's own process, discovery and vcvars copies in favour of sushicore (`cli/sushitrack_cli/proc.py`, `services/discovery.py`).`

Acceptance: the full suite passes with `proc.py` and `services/discovery.py` deleted.


---

### Task ST-DOCTOR: `st` adopts the shared commands

**Files:**
- Create: `D:/Projects/sushitrack/cli/sushitrack_cli/services/checks.py` (st's own checks)
- Modify: `D:/Projects/sushitrack/cli/sushitrack_cli/cli.py` (remove `doctor` command; register shared commands)
- Modify: `D:/Projects/sushitrack/cli/sushitrack_cli/services/diag.py` (delete `doctor`, `_check`, `_python_module` and imports only they used)
- Modify: `D:/Projects/sushitrack/cli/pyproject.toml` (`sushicore>=0.6.0`)
- Modify: `D:/Projects/sushitrack/docs/README.md` (command list: `setup`, `doctor [--for GROUP]`, `link`, `unlink`), `D:/Projects/sushitrack/docs/reference/CHANGELOG.md`
- Test: `D:/Projects/sushitrack/cli/tests/test_checks.py` (new), `D:/Projects/sushitrack/cli/tests/test_help_screen.py`

**Interfaces:**
- Consumes: `sushicore.provision.checks.path_check`, `python_module_check`, `tool_check`, `FunctionCheck`, `CheckResult`, `State`; `ModuleProvision`, `register_provision_commands`; `load_tool` from Task 5.
- Produces: `sushitrack_cli.services.checks.st_checks(paths: Paths) -> list[Check]`.

Groups: `build` — eigen submodule (required), docker (optional). `infer` — yolox submodule (`third_party/yolox/setup.py`), torch, torchvision, cv2, pycocotools (all optional so `st doctor` without `--for` still passes on a build-only machine). `eval` — TrackEval (`third_party/TrackEval/scripts/run_mot_challenge.py`), datasets (at least one `*/gt/gt.txt` under `paths.data_root()`), numpy, scipy (optional). Fixes: submodules → `git submodule update --init <path>`; Python modules → `pip install <pip name>` (`cv2` → `opencv-python`); datasets → `st doctor` points to the data section of `docs/README.md`.

- [ ] **Step 1: Failing tests** `tests/test_checks.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for SushiTrack's own doctor checks."""

from __future__ import annotations

from sushicore.provision.doctor import Doctor, State

from sushitrack_cli.services.checks import st_checks


def _by_name(checks):
    """Index checks by name."""
    return {c.name: c for c in checks}


def test_groups_cover_build_infer_and_eval(st_paths):
    """Assert every check sits in one of the groups the spec names."""
    groups = {c.group for c in st_checks(st_paths)}
    assert groups == {"build", "infer", "eval"}


def test_infer_group_names_the_spec_modules(st_paths):
    """Assert infer checks yolox, torch, torchvision, opencv and pycocotools."""
    names = {c.name for c in st_checks(st_paths) if c.group == "infer"}
    assert names == {"yolox", "torch", "torchvision", "cv2", "pycocotools"}


def test_missing_python_module_fix_names_the_pip_package(st_paths, monkeypatch):
    """Assert a missing cv2 is fixed by installing opencv-python."""
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    result = _by_name(st_checks(st_paths))["cv2"].run()
    assert result.state is State.FAIL
    assert result.fix == "pip install opencv-python"


def test_doctor_for_infer_runs_only_infer(st_paths, monkeypatch):
    """Assert restricting to infer leaves the eval and build checks out."""
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    report = Doctor(st_checks(st_paths)).run({"infer"})
    assert {row.check.group for row in report.rows} == {"infer"}
```

`st_paths` fixture in `conftest.py`: a `Paths` over a temp checkout with `third_party/eigen/Eigen/Dense` present and nothing else. Read `sushicore/provision/doctor.py` for `Report`'s real field names and adjust `report.rows`/`row.check` to them.

Append to `tests/test_help_screen.py`: assert `setup`, `doctor`, `link`, `unlink` all appear in `st --help`.

- [ ] **Step 2: Run** — FAIL.

- [ ] **Step 3: Implement** `services/checks.py` with one builder per check kind (`_submodule`, `_python`, `_datasets`) and `st_checks(paths)` listing them; `_python` wraps `python_module_check` and replaces its `fix` with `pip install <pip name>` from a module-level `_PIP_NAMES = {"cv2": "opencv-python"}`. In `cli.py`:

```python
register_provision_commands(app, ModuleProvision(
    profile=PROFILE,
    project_root=find_project_root,
    load_config=load_tool,
    console=lambda: console,
    extra_checks=lambda: st_checks(context()[1]),
))
```

Keep the new commands in the `K_DIAGNOSTICS` help panel if `register_provision_commands` allows a panel; if it does not, leave them in the default panel and report it (no sushicore change in this task).

- [ ] **Step 4: Run** st suite; `st doctor`, `st doctor --for infer`, `st setup --dry-run`, `st link --help`; paste.

Acceptance: st suite green; `st doctor` renders build/test/infer/eval rows and exits 0 on this machine.

---

## Final verification (controller)

sushicore, hub, sd and st suites; `hub doctor`; `st build`; `st test`; `st doctor`; `sd doctor`; `sd build`; every CLI `--help`. Then a whole-branch review per repo on `opus`.
