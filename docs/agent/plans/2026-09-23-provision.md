# Provision (sub-project 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move hub's install machinery into `sushicore.provision`, add the dependency root, registry, doctor, sinks and module commands, and make hub consume it through re-export modules without changing hub's behaviour.

**Architecture:** Additive subpackage in sushicore, layered bottom-up (config/output/home → system/probe/stamp → gpu/fragments/registry → packages → toolchains → pipeline/steps → doctor/checks → commands). Moved code keeps its behaviour and its on-disk layout; only imports and three seams change (console, config type, dependency root). Hub's old modules become re-exports.

**Tech Stack:** Python ≥3.10, rich, typer (optional extra), pytest.

**Spec:** `docs/agent/specs/2026-09-23-provision-design.md`

## Global Constraints

- Nothing installed on the owner's machine may break. Every CLI is a pipx editable install of its repo with its own non-editable copy of sushicore 0.4.0. sushicore repo edits are therefore invisible to installed tools; hub repo edits are live.
- No commit to `D:\Projects\sushistack` lands before Task 19 (injecting the new sushicore into hub's venv), and Task 19 runs only after the owner approves it.
- The public API of sushicore 0.4.0 stays unchanged. New code only adds.
- Moved code keeps its directory layout on disk (`toolchains/llvm-sycl`, `tools/`, `vcpkg/`, `ur/`). The versioned `toolchains/<name>/<version>/` layout belongs to sub-project 2, together with the migration.
- Dependency root: `SUSHISYSTEMS_HOME` env var, else `~/.sushisystems`. A consumer may bind its own root (hub binds `<workspace>/dependencies` until sub-project 2).
- Never invoke `se`, `cmake`, `ninja` or `ctest`. Tests run with `python -m pytest` only.
- Each hub test that moves with its module is deleted from hub in the same task; a hub test that also exercises hub-only code stays in hub and passes through the re-exports.
- Every file opens with the license block, a module docstring, and Google-style docstrings on every symbol (see `source-comments`). No TODOs.
- Commit messages follow `commits`; attribution line `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.

## Review Focus

1. `SUSHISYSTEMS_HOME` set to a relative path or with `~`: `home.root()` must return an absolute, expanded path. Pinned in Task 1.
2. A module outside any workspace, with no legacy tree: `home.legacy_roots()` returns `[]`, never raises. Pinned in Task 1.
3. `registry.toml` truncated or hand-edited to invalid TOML: `Registry.load()` raises `RegistryError` naming the file, it never silently empties the registry (which would let `remove` delete shared toolchains). Pinned in Task 5.
4. A second process holds `.lock`: the waiter times out with a message that names the holder PID, not a hang. Pinned in Task 5.
5. A check that raises instead of returning: `Doctor` reports it as `fail` with the exception text and keeps running the rest. Pinned in Task 6.

## Import rewrite table (used by every move task)

| Hub import | Replacement in sushicore |
| --- | --- |
| `from .. import console` / `from ... import console` | `from sushicore.provision._output import console` |
| `from ..config import Config` | `from sushicore.provision.config import ProvisionConfig` (annotation only) |
| `from ..config import deps_dir` / `deps_dir()` | `from sushicore.provision import home` / `home.root()` |
| `from .apt import …` | `from sushicore.provision.system import …` |
| `from .probe import …` | `from sushicore.provision.probe import …` |
| `from .toolchains import read_toolchain_stamp, record_toolchain_adapter, toolchain_adapter_commit, TOOLCHAIN_STAMP, has_sanitizer_runtime` | `from sushicore.provision.toolchains.stamp import …` |
| `from .gpu_backends.X import …` | `from sushicore.provision.gpu.X import …` |
| `from .dependency_source import Dependency, IDependencySource, SHARED_OWNER` | `from sushicore.provision.fragments import …` |
| `from .ordering import owner_order` | `from sushicore.provision.fragments import owner_order` |
| `from .package_managers import …` | `from sushicore.provision.packages import …` |
| `from .pipeline import …` | `from sushicore.provision.pipeline import …` |

Relative imports inside `sushicore.provision` are allowed and preferred (`from ..system import is_root`).

## Hub re-export shape (used by Tasks 20–22)

A hub module that moved becomes exactly this, with the names every hub importer uses:

```python
"""Re-export of :mod:`sushicore.provision.probe`; the implementation moved to sushicore."""

from sushicore.provision.probe import (  # noqa: F401
    binary_works,
    classify_display_adapters,
    detect_gpu_vendor,
    find_configured_toolchain,
    find_sycl_compiler,
    resolve_local_config,
    toolchain_status,
)
```

To list the names: `grep -rhoE "from \.+(setup\.)?probe import \(?[^)]*" D:/Projects/sushistack/cli --include=*.py` and the matching `import` lines in tests that stay in hub.

## Waves

| Wave | Tasks (parallel) | Files touched | Waits on | Verification after the wave |
| --- | --- | --- | --- | --- |
| 0 | 1 | `sushicore/provision/{__init__,_output,config,home}.py`, `tests/provision/{__init__,conftest,test_home,test_output}.py` | – | `python -m pytest -q` in sushicore |
| 1 | 2, 3, 4, 5, 6, 7, 14 | disjoint, listed per task | 1 | same |
| 2 | 8, 9, 10, 13 | disjoint | 2, 3, 4, 6, 7 | same |
| 3 | 11 | `provision/packages/` | 2, 9 | same |
| 4 | 12 | `provision/toolchains/{_process,intel_llvm,adaptivecpp,oneapi}.py` | 3, 11, 14 | same |
| 5 | 15 | `provision/steps.py` | 8, 12, 13 | same |
| 6 | 16 | `provision/commands.py` | 7, 10, 15 | same |
| 7 | 17, 18 | `tests/provision/test_layering.py`; `pyproject.toml`, `README.md`, `docs/reference/CHANGELOG.md` | 16 | same, plus hub's suite with `PYTHONPATH=D:/Projects/sushicore` |
| 8 | 19 (owner gate) | hub's pipx venv | 17, 18 | `hub --help`, `hub doctor` |
| 9 | 20, then 21, then 22 | `sushistack/cli/...`, split per task | 19 | hub's suite, then `hub doctor` |

Wave 9 runs serially: hub's working tree is what the installed `hub` executes, so each task must leave it working before the next starts.

---

### Task 1: Foundation — output seam, config protocol, dependency root

**Files:**
- Create: `sushicore/provision/__init__.py`, `sushicore/provision/_output.py`, `sushicore/provision/config.py`, `sushicore/provision/home.py`
- Test: `tests/provision/__init__.py` (empty), `tests/provision/conftest.py`, `tests/provision/test_home.py`, `tests/provision/test_output.py`

**Interfaces:**
- Produces:
  - `sushicore.provision._output.console` — a proxy; attribute access resolves on the bound console.
  - `sushicore.provision.bind_console(provider: Callable[[], Console]) -> None`
  - `sushicore.provision.config.ProvisionConfig` (Protocol), `ProvisionSettings(ToolConfig)` dataclass
  - `sushicore.provision.home`: `ENV_HOME = "SUSHISYSTEMS_HOME"`, `DIR_NAME = ".sushisystems"`, `default_root() -> Path`, `bind_root(provider: Callable[[], Path] | None) -> None`, `root() -> Path`, `legacy_roots() -> list[Path]`, `search_roots() -> list[Path]`, `toolchains_dir() -> Path`, `tools_dir() -> Path`, `vcpkg_dir() -> Path`, `ur_dir() -> Path`, `build_dir() -> Path`
  - fixtures in `tests/provision/conftest.py`: `recording_console` (binds a `RecordingConsole`, yields it, unbinds), `provision_home` (sets `SUSHISYSTEMS_HOME` to a tmp dir, clears any bound root, yields the path)

- [ ] **Step 1: Write the failing tests**

`tests/provision/conftest.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Fixtures shared by the provision tests."""

from __future__ import annotations

import pytest

from sushicore import provision
from sushicore.provision import home


class RecordingConsole:
    """Collects every console call as ``(method, args)`` for assertions."""

    def __init__(self) -> None:
        """Start with no recorded calls."""
        self.calls: list[tuple[str, tuple]] = []

    def __getattr__(self, name: str):
        """Return a recorder for any console method name."""
        def record(*args, **_kwargs):
            self.calls.append((name, args))
        return record


@pytest.fixture
def recording_console():
    """Bind a recording console for the test, then unbind it."""
    fake = RecordingConsole()
    provision.bind_console(lambda: fake)
    yield fake
    provision.bind_console(None)


@pytest.fixture
def provision_home(tmp_path, monkeypatch):
    """Point the dependency root at a temporary directory."""
    root = tmp_path / "sushisystems"
    monkeypatch.setenv(home.ENV_HOME, str(root))
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    monkeypatch.delenv("SUSHISTACK_DEPS_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    home.bind_root(None)
    yield root
    home.bind_root(None)
```

`tests/provision/test_home.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the dependency root resolution."""

from __future__ import annotations

from pathlib import Path

from sushicore.provision import home


def test_default_root_is_in_the_user_home(monkeypatch):
    monkeypatch.delenv(home.ENV_HOME, raising=False)
    home.bind_root(None)
    assert home.root() == Path.home() / ".sushisystems"


def test_env_var_wins_and_is_expanded_and_absolute(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(home.ENV_HOME, "relative/deps")
    home.bind_root(None)
    assert home.root() == (tmp_path / "relative" / "deps").resolve()


def test_bound_root_wins_over_env(provision_home, tmp_path):
    bound = tmp_path / "bound"
    home.bind_root(lambda: bound)
    assert home.root() == bound.resolve()


def test_subdirectories_hang_off_the_root(provision_home):
    assert home.toolchains_dir() == provision_home.resolve() / "toolchains"
    assert home.tools_dir() == provision_home.resolve() / "tools"
    assert home.vcpkg_dir() == provision_home.resolve() / "vcpkg"
    assert home.ur_dir() == provision_home.resolve() / "ur"
    assert home.build_dir() == provision_home.resolve() / "build"


def test_no_legacy_root_outside_a_workspace(provision_home):
    assert home.legacy_roots() == []
    assert home.search_roots() == [home.root()]


def test_workspace_dependencies_is_a_legacy_root(provision_home, tmp_path, monkeypatch):
    ws = tmp_path / "ws"
    (ws / ".sushistack").mkdir(parents=True)
    (ws / "dependencies").mkdir()
    monkeypatch.chdir(ws)
    assert home.legacy_roots() == [(ws / "dependencies").resolve()]
    assert home.search_roots() == [home.root(), (ws / "dependencies").resolve()]


def test_legacy_env_override_is_a_legacy_root(provision_home, tmp_path, monkeypatch):
    legacy = tmp_path / "old"
    legacy.mkdir()
    monkeypatch.setenv("SUSHISTACK_DEPS_DIR", str(legacy))
    assert home.legacy_roots() == [legacy.resolve()]


def test_the_bound_root_is_never_its_own_legacy_root(provision_home, tmp_path, monkeypatch):
    ws = tmp_path / "ws"
    (ws / ".sushistack").mkdir(parents=True)
    (ws / "dependencies").mkdir()
    monkeypatch.chdir(ws)
    home.bind_root(lambda: ws / "dependencies")
    assert home.legacy_roots() == []
```

`tests/provision/test_output.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the console seam moved code prints through."""

from __future__ import annotations

import pytest

from sushicore import provision
from sushicore.provision._output import console


def test_calls_reach_the_bound_console(recording_console):
    console.info("hello")
    assert recording_console.calls == [("info", ("hello",))]


def test_unbound_console_raises_a_named_error():
    provision.bind_console(None)
    with pytest.raises(RuntimeError, match="bind_console"):
        console.info("x")


def test_provider_is_called_lazily():
    calls = []

    class Fake:
        def info(self, msg):
            calls.append(msg)

    provision.bind_console(lambda: Fake())
    assert calls == []
    console.info("late")
    assert calls == ["late"]
    provision.bind_console(None)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd D:/Projects/sushicore && python -m pytest tests/provision -q`
Expected: collection errors, `ModuleNotFoundError: No module named 'sushicore.provision'`.

- [ ] **Step 3: Implement**

`sushicore/provision/__init__.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Dependency provisioning shared by hub and every module CLI.

See ``docs/agent/specs/2026-09-23-provision-design.md``.
"""

from ._output import bind_console

__all__ = ["bind_console"]
```

`sushicore/provision/_output.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The one console every provision module prints through, bound by the consuming CLI."""

from __future__ import annotations

from typing import Callable

_provider: Callable[[], object] | None = None


def bind_console(provider: Callable[[], object] | None) -> None:
    """Set the callable that returns the console provision prints through.

    Args:
        provider: Returns a :class:`sushicore.console.Console`; called on each use,
            so a lazily built console stays lazy. ``None`` unbinds.
    """
    global _provider
    _provider = provider


class _ConsoleProxy:
    """Forwards every attribute to the console the bound provider returns."""

    def __getattr__(self, name: str):
        """Resolve *name* on the bound console."""
        if _provider is None:
            raise RuntimeError(
                "sushicore.provision has no console; call "
                "sushicore.provision.bind_console(provider) first.")
        return getattr(_provider(), name)


console = _ConsoleProxy()
```

`sushicore/provision/config.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The configuration shape provision code reads, and a concrete one for standalone modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..config_base import ToolConfig


class ProvisionConfig(Protocol):
    """The fields and helpers provision code reads from a CLI's config."""

    platform: str
    cmake_exe: str
    ninja_exe: str
    vs_vcvars: str
    vcpkg_root: str
    vcpkg_triplet: str
    pkgconf_exe: str
    doxygen_exe: str
    oneapi_root: str
    icx_compiler: str
    llvm_root: str
    acpp_exe: str

    @property
    def is_windows(self) -> bool:
        """Report whether the config was resolved for Windows."""

    def expand(self, value: str) -> str:
        """Expand ``~`` and environment variables in a path value."""


@dataclass
class ProvisionSettings(ToolConfig):
    """A :class:`ToolConfig` carrying the toolchain roots provision probes and writes."""

    oneapi_root: str = ""
    icx_compiler: str = ""
    llvm_root: str = ""
    acpp_exe: str = ""
```

`sushicore/provision/home.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Resolves the machine's dependency root and the legacy trees read alongside it."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from ..workspace import WORKSPACE_MARKER, has_marker, resolve_env_path, walk_up

ENV_HOME = "SUSHISYSTEMS_HOME"
DIR_NAME = ".sushisystems"
_LEGACY_ENV = "SUSHISTACK_DEPS_DIR"

_bound: Callable[[], Path] | None = None


def default_root() -> Path:
    """Return ``~/.sushisystems``."""
    return Path.home() / DIR_NAME


def bind_root(provider: Callable[[], Path] | None) -> None:
    """Make *provider* the source of the root, overriding the env var; ``None`` unbinds."""
    global _bound
    _bound = provider


def root() -> Path:
    """Return the absolute dependency root: bound provider, then env var, then default."""
    if _bound is not None:
        return Path(_bound()).expanduser().resolve()
    value = os.environ.get(ENV_HOME)
    if value:
        return Path(os.path.expandvars(os.path.expanduser(value))).resolve()
    return default_root()


def legacy_roots() -> list[Path]:
    """Return existing hub trees read as installed, excluding the current root."""
    found: list[Path] = []
    override = resolve_env_path(_LEGACY_ENV)
    if override is not None:
        found.append(override)
    workspace = resolve_env_path("SUSHISTACK_HOME") or walk_up(
        Path.cwd(), has_marker(WORKSPACE_MARKER))
    if workspace is not None:
        found.append((workspace / "dependencies").resolve())
    current = root()
    result: list[Path] = []
    for path in found:
        if path.is_dir() and path != current and path not in result:
            result.append(path)
    return result


def search_roots() -> list[Path]:
    """Return the root followed by every legacy root, in lookup order."""
    return [root(), *legacy_roots()]


def toolchains_dir() -> Path:
    """Return ``<root>/toolchains``."""
    return root() / "toolchains"


def tools_dir() -> Path:
    """Return ``<root>/tools``."""
    return root() / "tools"


def vcpkg_dir() -> Path:
    """Return ``<root>/vcpkg``."""
    return root() / "vcpkg"


def ur_dir() -> Path:
    """Return ``<root>/ur``."""
    return root() / "ur"


def build_dir() -> Path:
    """Return ``<root>/build``."""
    return root() / "build"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd D:/Projects/sushicore && python -m pytest -q`
Expected: all pass (409 existing + 11 new).

- [ ] **Step 5: Commit**

```bash
cd D:/Projects/sushicore
git add sushicore/provision tests/provision
git commit -m "feat(provision): add the console seam, config protocol and dependency root"
```

---

### Task 2: System helpers and tool probing

**Files:**
- Create: `sushicore/provision/system.py` from `D:/Projects/sushistack/cli/sushihub/setup/apt.py` (all of it: `is_root`, `os_release`, `sudo_bash`, `ensure_intel_oneapi_repo` and their constants); `sushicore/provision/probe.py` from `sushihub/setup/probe.py` **without** `write_platform_paths` and `render_local_config` (those go to Task 8).
- Test: `tests/provision/test_probe.py`, `tests/provision/test_system.py`

**Interfaces:**
- Consumes: Task 1 (`console`, `ProvisionConfig`, `home`).
- Produces: `system.is_root() -> bool`, `system.os_release() -> dict[str, str]`, `system.sudo_bash(cmd: str, dry_run: bool) -> bool`, `system.ensure_intel_oneapi_repo(dry_run: bool) -> bool`; `probe.binary_works(cmd: str) -> bool`, `probe.toolchain_status(cfg, gpu: bool) -> list[tuple[str, bool, str]]`, `probe.detect_gpu_vendor() -> str`, `probe.classify_display_adapters(adapters: str) -> str`, `probe.is_integrated_adapter(line: str) -> bool`, `probe.find_sycl_compiler(cfg) -> tuple[str | None, str]`, `probe.find_configured_toolchain(cfg) -> tuple[str | None, str]`, `probe.resolve_local_config(cfg, gpu: bool = False) -> dict[str, str]` — signatures identical to hub's, `cfg` typed `ProvisionConfig`.

- [ ] **Step 1: Copy and rewrite imports**

Copy both files byte for byte, then apply the import rewrite table. In `probe.py` replace `_tools_dir()` and `_toolchains_dir()` bodies with `return home.tools_dir()` and `return home.toolchains_dir()`, and remove the `WORKSPACE_HEADER` import together with the two functions Task 8 owns. Replace every `Config` annotation with `ProvisionConfig`.

- [ ] **Step 2: Write the tests**

`tests/provision/test_probe.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for tool probing."""

from __future__ import annotations

from sushicore.provision import probe


def test_classify_prefers_a_discrete_adapter():
    adapters = "Intel(R) UHD Graphics 770\nNVIDIA GeForce RTX 4070\n"
    assert probe.classify_display_adapters(adapters) == "nvidia"


def test_integrated_only_is_none():
    assert probe.classify_display_adapters("Intel(R) UHD Graphics 770\n") == "none"


def test_binary_works_rejects_a_missing_command():
    assert probe.binary_works("sushi-no-such-binary-xyz") is False


def test_tools_dir_follows_the_root(provision_home):
    assert probe._tools_dir() == provision_home.resolve() / "tools"
```

`tests/provision/test_system.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the OS helpers."""

from __future__ import annotations

from sushicore.provision import system


def test_sudo_bash_dry_run_runs_nothing(recording_console):
    assert system.sudo_bash("false", dry_run=True) is True


def test_os_release_is_a_dict():
    assert isinstance(system.os_release(), dict)
```

Before writing these, read hub's `probe.classify_display_adapters` and `apt.sudo_bash`; if a literal above disagrees with hub's behaviour (return value on dry run, vendor names), change the test to hub's behaviour, never the code.

- [ ] **Step 3: Run**

Run: `cd D:/Projects/sushicore && python -m pytest tests/provision -q`
Expected: pass.

- [ ] **Step 4: Commit**

```bash
git add sushicore/provision/system.py sushicore/provision/probe.py tests/provision/test_probe.py tests/provision/test_system.py
git commit -m "feat(provision): move the OS helpers and tool probing from hub"
```

---

### Task 3: Toolchain stamp, compiler identity, Windows installer plumbing

**Files:**
- Create: `sushicore/provision/toolchains/__init__.py` (docstring only), `toolchains/stamp.py`, `sushicore/provision/gpu/__init__.py` (docstring only), `gpu/compiler_identity.py`, `gpu/windows_installer.py`
- Move tests: `sushistack/cli/tests/test_compiler_identity.py` → `tests/provision/test_compiler_identity.py`; the stamp-only tests from `test_toolchains.py` → `tests/provision/test_stamp.py` (a test stays in hub if it calls `install_intel_llvm` or `install_adaptivecpp`; Task 12 moves those)
- Test: `tests/provision/test_stamp.py`

**Interfaces:**
- Produces: `stamp.TOOLCHAIN_STAMP = ".sushi_toolchain.json"`, `stamp.toolchains_dir() -> Path` (returns `home.toolchains_dir()`), `stamp.read_toolchain_stamp(root: Path) -> dict`, `stamp.write_toolchain_stamp(root: Path, source: str, tag: str) -> None` (hub's `_write_toolchain_stamp`, made public), `stamp.record_toolchain_adapter(root: Path, vendor: str, commit: str) -> None`, `stamp.toolchain_adapter_commit(root: Path, vendor: str) -> str | None`, `stamp.has_sanitizer_runtime(root: Path) -> bool`; `compiler_identity.read_intel_llvm_commit(...)` unchanged; `windows_installer.*` unchanged, `deps_dir()` → `home.root()`.

- [ ] **Step 1: Write the failing test**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the toolchain provenance stamp."""

from __future__ import annotations

from sushicore.provision.toolchains import stamp


def test_missing_stamp_reads_empty(tmp_path):
    assert stamp.read_toolchain_stamp(tmp_path) == {}


def test_written_stamp_round_trips(tmp_path):
    stamp.write_toolchain_stamp(tmp_path, "intel/llvm", "nightly-2026-09-01")
    data = stamp.read_toolchain_stamp(tmp_path)
    assert data["source"] == "intel/llvm"
    assert data["tag"] == "nightly-2026-09-01"


def test_adapter_commit_is_recorded_without_losing_the_tag(tmp_path):
    stamp.write_toolchain_stamp(tmp_path, "intel/llvm", "t")
    stamp.record_toolchain_adapter(tmp_path, "cuda", "abc123")
    assert stamp.toolchain_adapter_commit(tmp_path, "cuda") == "abc123"
    assert stamp.read_toolchain_stamp(tmp_path)["tag"] == "t"


def test_toolchains_dir_follows_the_root(provision_home):
    assert stamp.toolchains_dir() == provision_home.resolve() / "toolchains"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/provision/test_stamp.py -q` → `ModuleNotFoundError`.

- [ ] **Step 3: Implement** by copying `TOOLCHAIN_STAMP`, `toolchains_dir`, `read_toolchain_stamp`, `_rewrite_stamp`, `_write_toolchain_stamp` (renamed `write_toolchain_stamp`), `record_toolchain_adapter`, `toolchain_adapter_commit` and `has_sanitizer_runtime` from `sushihub/setup/toolchains.py` into `stamp.py`; copy `gpu_backends/compiler_identity.py` and `gpu_backends/windows_installer.py`; apply the rewrite table.

- [ ] **Step 4: Run** `python -m pytest tests/provision -q` → pass.

- [ ] **Step 5: Commit**

```bash
git add sushicore/provision/toolchains sushicore/provision/gpu tests/provision/test_stamp.py tests/provision/test_compiler_identity.py
git commit -m "feat(provision): move the toolchain stamp and GPU installer plumbing from hub"
```

---

### Task 4: Fragment aggregation

**Files:**
- Create: `sushicore/provision/fragments.py` from `sushihub/setup/dependency_source.py` (`SHARED_OWNER`, `Dependency`, `_merge_ports`, `_merge`, `IDependencySource`, `_parse_manifest`, `TomlDependencySource`) and `sushihub/setup/ordering.py` (`owner_order`). **Not** moved: `MODULE_MANIFEST_REL`, `MANIFESTS_DIR`, `SHIPPED_MANIFEST_SUFFIX`, `SHARED_MANIFEST_STEM`, `_owner_for_shipped`, `packaged_manifests`, `manifest_sources`, `manifest_paths` (hub-only workspace discovery).
- Move tests: `test_dependency_merge.py`, `test_ordering.py` → `tests/provision/`

**Interfaces:**
- Produces: `fragments.SHARED_OWNER = "shared"`, `fragments.Dependency` (hub's subclass, fields unchanged, `vcpkg_fallback_ports(platform) -> list[str]`), `fragments.IDependencySource` (ABC: `all() -> list[Dependency]`, `selected(platform: str, gpu: bool) -> list[Dependency]`, `depends_on(owner: str) -> list[str]` — keep hub's exact method set), `fragments.TomlDependencySource(sources: list[tuple[Path, str]])` — **change**: the source list is a required constructor argument instead of calling `manifest_sources()`; `fragments.owner_order(source, owners) -> list[str]`.

- [ ] **Step 1: Write the failing test** `tests/provision/test_fragment_source.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the fragment source taking an explicit list of files."""

from __future__ import annotations

from sushicore.provision.fragments import SHARED_OWNER, TomlDependencySource


def _write(path, body):
    path.write_text(body, encoding="utf-8")
    return path


def test_source_reads_only_the_files_it_is_given(tmp_path, recording_console):
    mine = _write(tmp_path / "mine.deps.toml", '[gtest]\ndescription = "t"\nrequired = false\n'
                  'linux_apt = ["libgtest-dev"]\nwindows_vcpkg = ["gtest"]\n')
    source = TomlDependencySource([(mine, "sushitrack")])
    deps = source.all()
    assert [d.name for d in deps] == ["gtest"]
    assert deps[0].owner == "sushitrack"


def test_same_named_deps_merge_across_files(tmp_path, recording_console):
    a = _write(tmp_path / "a.deps.toml", '[x]\ndescription = "a"\nrequired = false\n'
               'linux_apt = ["p1"]\nwindows_vcpkg = []\n')
    b = _write(tmp_path / "b.deps.toml", '[x]\ndescription = "b"\nrequired = true\n'
               'linux_apt = ["p2"]\nwindows_vcpkg = []\n')
    (dep,) = TomlDependencySource([(a, SHARED_OWNER), (b, "m")]).all()
    assert dep.required is True
    assert dep.linux_apt == ["p1", "p2"]
```

- [ ] **Step 2: Run** → fails with `ModuleNotFoundError`.
- [ ] **Step 3: Implement** by copying the listed symbols, applying the rewrite table, and changing `TomlDependencySource.__init__` to store the given list where hub called `manifest_sources()`. In the moved `test_dependency_merge.py` and `test_ordering.py`, construct sources with an explicit list wherever the hub test monkeypatched `manifest_sources`.
- [ ] **Step 4: Run** `python -m pytest tests/provision -q` → pass.
- [ ] **Step 5: Commit** `feat(provision): move fragment merging from hub behind an explicit source list`.

---

### Task 5: Component registry and lock

**Files:**
- Create: `sushicore/provision/lock.py`, `sushicore/provision/registry.py`
- Test: `tests/provision/test_lock.py`, `tests/provision/test_registry.py`

**Interfaces:**
- Consumes: Task 1 `home`, Task 3 `stamp` is **not** consumed (stamp rebuild is Task 10's check).
- Produces:
  - `lock.ProvisionLock(path: Path, timeout: float = 600.0)`, context manager; on timeout raises `LockTimeout` whose message includes the holder PID read from the lock file.
  - `registry.Component` frozen dataclass: `name: str, version: str, path: str, source: str, installed_at: str, consumers: tuple[str, ...]`
  - `registry.RegistryError(Exception)`
  - `registry.Registry(path: Path)`: `load() -> None`, `components() -> list[Component]`, `find(name: str, version: str | None = None) -> Component | None`, `add(component: Component) -> None` (merges consumers when name+version exists), `release(name: str, version: str, consumer: str) -> bool` (removes the consumer; returns True when no consumer is left), `save() -> None` (temp file + `os.replace`)
  - `registry.default_path() -> Path` = `home.root() / "registry.toml"`

- [ ] **Step 1: Write the failing tests**

`tests/provision/test_registry.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the installed-component registry."""

from __future__ import annotations

import pytest

from sushicore.provision.registry import Component, Registry, RegistryError


def _llvm(consumer):
    return Component("intel-llvm", "nightly-1", "/x", "intel/llvm", "2026-09-23T00:00:00Z",
                     (consumer,))


def test_empty_registry_has_no_components(tmp_path):
    reg = Registry(tmp_path / "registry.toml")
    reg.load()
    assert reg.components() == []


def test_add_save_load_round_trips(tmp_path):
    path = tmp_path / "registry.toml"
    reg = Registry(path)
    reg.load()
    reg.add(_llvm("sushidsp"))
    reg.save()
    again = Registry(path)
    again.load()
    assert again.find("intel-llvm", "nightly-1").consumers == ("sushidsp",)


def test_second_consumer_merges_instead_of_duplicating(tmp_path):
    reg = Registry(tmp_path / "r.toml")
    reg.load()
    reg.add(_llvm("sushidsp"))
    reg.add(_llvm("sushiruntime"))
    assert len(reg.components()) == 1
    assert set(reg.find("intel-llvm").consumers) == {"sushidsp", "sushiruntime"}


def test_release_keeps_a_component_another_consumer_uses(tmp_path):
    reg = Registry(tmp_path / "r.toml")
    reg.load()
    reg.add(_llvm("sushidsp"))
    reg.add(_llvm("sushiruntime"))
    assert reg.release("intel-llvm", "nightly-1", "sushidsp") is False
    assert reg.release("intel-llvm", "nightly-1", "sushiruntime") is True


def test_corrupt_registry_raises_instead_of_emptying(tmp_path):
    path = tmp_path / "registry.toml"
    path.write_text("[[component]\nname = ", encoding="utf-8")
    with pytest.raises(RegistryError, match="registry.toml"):
        Registry(path).load()


def test_save_leaves_no_temp_file(tmp_path):
    reg = Registry(tmp_path / "r.toml")
    reg.load()
    reg.add(_llvm("a"))
    reg.save()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["r.toml"]
```

`tests/provision/test_lock.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the provisioning file lock."""

from __future__ import annotations

import os

import pytest

from sushicore.provision.lock import LockTimeout, ProvisionLock


def test_lock_is_released_on_exit(tmp_path):
    path = tmp_path / ".lock"
    with ProvisionLock(path):
        pass
    with ProvisionLock(path, timeout=0.5):
        pass


def test_second_holder_times_out_naming_the_pid(tmp_path):
    path = tmp_path / ".lock"
    with ProvisionLock(path):
        with pytest.raises(LockTimeout, match=str(os.getpid())):
            with ProvisionLock(path, timeout=0.3):
                pass
```

- [ ] **Step 2: Run** → `ModuleNotFoundError`.
- [ ] **Step 3: Implement.** The file format is:

```toml
# Components installed under this dependency root. Written by sushicore.provision.
[[component]]
name = "intel-llvm"
version = "nightly-1"
path = "/x"
source = "intel/llvm"
installed_at = "2026-09-23T00:00:00Z"
consumers = ["sushidsp"]
```

`registry.py` parses with `sushicore.workspace.read_toml` semantics but must distinguish "missing" from "invalid": use `tomllib.load` directly and wrap `tomllib.TOMLDecodeError` into `RegistryError(f"{path}: {exc}")`. Writing renders the list by hand (TOML has no stdlib writer): each value through `json.dumps` for strings and `"[" + ", ".join(json.dumps(c) for c in consumers) + "]"` for the list; write to `path.with_suffix(".toml.tmp")`, then `os.replace`.

`lock.py` creates the lock file with `os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)`, writes the PID, and polls every 0.1 s until `timeout`; on exit it deletes the file. A lock file whose PID no longer runs is stale: remove it and retry (check with `os.kill(pid, 0)` on POSIX and `ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)` on Windows, each behind one helper `_pid_alive(pid) -> bool`).

- [ ] **Step 4: Run** `python -m pytest tests/provision -q` → pass.
- [ ] **Step 5: Commit** `feat(provision): add the component registry and the provisioning lock`.

---

### Task 6: Doctor framework

**Files:**
- Create: `sushicore/provision/doctor.py`
- Test: `tests/provision/test_doctor.py`

**Interfaces:**
- Produces:
  - `State(enum.Enum)`: `OK="ok"`, `WARN="warn"`, `FAIL="fail"`, `SKIP="skip"`
  - `CheckResult` frozen dataclass: `state: State`, `detail: str`, `fix: str = ""`
  - `Check(Protocol)`: `name: str`, `group: str`, `required: bool`, `run(self) -> CheckResult`
  - `FunctionCheck(name, group, required, fn: Callable[[], CheckResult])` concrete adapter
  - `Report` frozen dataclass: `rows: tuple[tuple[Check, CheckResult], ...]`; `failures() -> int` (required checks in `FAIL`), `exit_code() -> int`
  - `Doctor(checks: Sequence[Check])`: `run(groups: Collection[str] | None = None) -> Report`, `render(report: Report, console) -> None` (table `["Check", "Group", "Result", "Detail", "Fix"]`, then `console.result(ok, {"checks": [...]})`)
  - `GROUPS = ("build", "test", "infer", "eval")`

- [ ] **Step 1: Write the failing tests**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the doctor framework."""

from __future__ import annotations

from sushicore.provision.doctor import CheckResult, Doctor, FunctionCheck, State


def _check(name, group, required, state, fix=""):
    return FunctionCheck(name, group, required, lambda: CheckResult(state, name, fix))


def test_required_failure_sets_exit_code_one():
    report = Doctor([_check("cmake", "build", True, State.FAIL)]).run()
    assert report.failures() == 1
    assert report.exit_code() == 1


def test_optional_failure_only_warns():
    report = Doctor([_check("docker", "build", False, State.FAIL)]).run()
    assert report.exit_code() == 0


def test_group_filter_runs_only_that_group():
    report = Doctor([_check("cmake", "build", True, State.OK),
                     _check("torch", "infer", True, State.FAIL)]).run(groups={"build"})
    assert [c.name for c, _ in report.rows] == ["cmake"]
    assert report.exit_code() == 0


def test_a_raising_check_is_a_failure_and_the_rest_still_run():
    def boom():
        raise OSError("disk gone")
    report = Doctor([FunctionCheck("x", "build", True, boom),
                     _check("y", "build", True, State.OK)]).run()
    states = [(c.name, r.state) for c, r in report.rows]
    assert states == [("x", State.FAIL), ("y", State.OK)]
    assert "disk gone" in report.rows[0][1].detail


def test_render_prints_a_table_and_a_result(recording_console):
    doctor = Doctor([_check("cmake", "build", True, State.OK, fix="st setup")])
    doctor.render(doctor.run(), recording_console)
    methods = [m for m, _ in recording_console.calls]
    assert methods == ["table", "result"]
```

- [ ] **Step 2: Run** → fails.
- [ ] **Step 3: Implement.** `run` wraps each `check.run()` in `try/except Exception as exc` and returns `CheckResult(State.FAIL, f"{type(exc).__name__}: {exc}")`. `render` builds rows `[name, group, markup, detail, fix]` where markup is `[success]ok[/success]`, `[warn]warn[/warn]`, `[error]FAIL[/error]` (FAIL on a non-required check renders as `[warn]warn[/warn]`), `[dim]skip[/dim]`, and calls `console.table([...], rows, title="Doctor")` then `console.result(report.exit_code() == 0, {"checks": [{"name", "group", "required", "state", "detail", "fix"}]})`.
- [ ] **Step 4: Run** → pass.
- [ ] **Step 5: Commit** `feat(provision): add the doctor framework`.

---

### Task 7: `[modules]` table owned by sushicore

**Files:**
- Modify: `sushicore/workspace.py` (append; nothing existing changes)
- Test: `tests/test_workspace_modules.py`

**Interfaces:**
- Produces: `WORKSPACE_VERSION = "1"`, `WORKSPACE_HEADER: list[str]` (hub's exact six lines), `registered_modules(root: Path) -> dict[str, str]`, `write_module(root: Path, name: str, path: Path) -> Path`, `remove_module(root: Path, name: str) -> bool`. All three take the workspace root explicitly; none walks up on its own.

- [ ] **Step 1: Write the failing tests**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the workspace [modules] table."""

from __future__ import annotations

from sushicore.workspace import (
    read_toml, registered_modules, remove_module, workspace_file, write_module)


def test_no_file_means_no_modules(tmp_path):
    assert registered_modules(tmp_path) == {}


def test_write_then_read(tmp_path):
    write_module(tmp_path, "sushidsp", tmp_path / "dsp")
    assert registered_modules(tmp_path) == {"sushidsp": str(tmp_path / "dsp")}


def test_write_keeps_the_tool_table(tmp_path):
    target = workspace_file(tmp_path)
    target.parent.mkdir(parents=True)
    target.write_text('[tool.windows]\ncmake_exe = "C:/cmake.exe"\n', encoding="utf-8")
    write_module(tmp_path, "sushidsp", tmp_path / "dsp")
    doc = read_toml(target)
    assert doc["tool"]["windows"]["cmake_exe"] == "C:/cmake.exe"
    assert doc["workspace"]["version"] == "1"


def test_remove_reports_whether_it_removed(tmp_path):
    write_module(tmp_path, "a", tmp_path)
    assert remove_module(tmp_path, "a") is True
    assert remove_module(tmp_path, "a") is False
    assert registered_modules(tmp_path) == {}
```

- [ ] **Step 2: Run** → `ImportError`.
- [ ] **Step 3: Implement** by porting `sushihub/services/links.py` `registered` and `write` with `root` passed in, using `config_base.write_toml_document(target, document, WORKSPACE_HEADER)`. Import `write_toml_document` inside the functions: `config_base` imports `workspace`, so a module-level import would be circular.
- [ ] **Step 4: Run** `python -m pytest -q` → pass.
- [ ] **Step 5: Commit** `feat(workspace): own the [modules] table so modules can link without hub`.

---

### Task 14: Pipeline core and toolchain selection

**Files:**
- Create: `sushicore/provision/pipeline.py` from `sushihub/setup/pipeline.py` plus `ToolchainSelection` from `sushihub/setup/selection.py` (the dataclass with `as_dict` and `merged`; **not** `components`, `MACHINE_COMPONENTS` or `selection_from_source`, which read hub's `CUSTOMIZABLE_COMPONENTS`)
- Test: `tests/provision/test_pipeline.py`

**Interfaces:**
- Produces: `StepResult`, `Step`, `InstallPipeline` unchanged; `ToolchainSelection(install_intel_llvm: bool = False, install_acpp: bool = False, oneapi: bool = False, gpu: bool = False)` with `as_dict()`, `merged(overrides)`, `from_context` **removed**; `InstallContext` becomes:

```python
@dataclass
class InstallContext:
    """State shared across steps for one installer run."""

    cfg: ProvisionConfig
    selection: ToolchainSelection = field(default_factory=ToolchainSelection)
    consumer: str = ""
    dry_run: bool = False
    everything: bool = False
    active_toolchain: str | None = None
    refresh_toolchains: bool = False
    assume_acpp_llvm: bool = False
    gpu_vendor: str = ""
    warnings: list[str] = field(default_factory=list)
    detected: dict[str, bool] = field(default_factory=dict)
    installed: list[str] = field(default_factory=list)
    resolved_paths: dict[str, str] = field(default_factory=dict)

    @property
    def gpu(self) -> bool:
        """Report whether this run provisions the GPU toolkit."""
        return self.selection.gpu
```

`consumer` is the module name recorded in the registry. Code that read `ctx.install_intel_llvm`, `ctx.install_acpp` or `ctx.oneapi` reads `ctx.selection.<same name>`.

- [ ] **Step 1: Write the failing tests**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the pipeline core."""

from __future__ import annotations

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.pipeline import (
    InstallContext, InstallPipeline, Step, StepResult, ToolchainSelection)


class _Step(Step):
    def __init__(self, name, result, log):
        self.name, self._result, self._log = name, result, log

    def run(self, ctx):
        self._log.append(self.name)
        return self._result


def test_pipeline_stops_on_the_first_failure(recording_console):
    log = []
    steps = [_Step("a", StepResult.OK, log), _Step("b", StepResult.FAILED, log),
             _Step("c", StepResult.OK, log)]
    ok = InstallPipeline(steps).run(InstallContext(cfg=ProvisionSettings()), show_progress=False)
    assert ok is False
    assert log == ["a", "b"]


def test_empty_selection_installs_nothing():
    assert ToolchainSelection().as_dict() == {
        "install_intel_llvm": False, "install_acpp": False, "oneapi": False, "gpu": False}


def test_gpu_reads_through_the_selection():
    ctx = InstallContext(cfg=ProvisionSettings(), selection=ToolchainSelection(gpu=True))
    assert ctx.gpu is True
```

- [ ] **Step 2: Run** → fails. **Step 3: Implement** as above; the progress block keeps `console.console` for Rich. **Step 4: Run** → pass. **Step 5: Commit** `feat(provision): move the install pipeline and group its toolchain options`.

---

### Task 8: Config sinks

**Files:**
- Create: `sushicore/provision/sinks.py` (also receives hub `probe.write_platform_paths` and `probe.render_local_config`)
- Test: `tests/provision/test_sinks.py`

**Interfaces:**
- Consumes: Task 7 `WORKSPACE_HEADER`, `workspace_file`.
- Produces: `ConfigSink(Protocol)`: `target: Path`, `write_paths(platform: str, values: dict[str, str]) -> Path`, `write_tool(updates: dict[str, str]) -> Path`, `clear() -> None`; `WorkspaceSink(root: Path)` (target `workspace_file(root)`, header `WORKSPACE_HEADER`); `ModuleSink(config_dir: Path, header: list[str])` (target `config_dir / "config.local.toml"`); free functions `write_platform_paths(target, platform, values, header) -> Path`, `render_local_config(platform, values) -> str`.

- [ ] **Step 1: Write the failing tests**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for where ConfigureStep's results are written."""

from __future__ import annotations

from sushicore.provision.sinks import ModuleSink, WorkspaceSink
from sushicore.workspace import read_toml, workspace_file, write_module


def test_module_sink_writes_config_local(tmp_path):
    sink = ModuleSink(tmp_path, ["# test"])
    sink.write_paths("windows", {"cmake_exe": "C:/cmake.exe"})
    assert read_toml(tmp_path / "config.local.toml")["tool"]["windows"]["cmake_exe"] == "C:/cmake.exe"


def test_workspace_sink_keeps_modules(tmp_path):
    write_module(tmp_path, "sushidsp", tmp_path)
    WorkspaceSink(tmp_path).write_paths("linux", {"ninja_exe": "/usr/bin/ninja"})
    doc = read_toml(workspace_file(tmp_path))
    assert doc["modules"]["sushidsp"] == str(tmp_path)
    assert doc["tool"]["linux"]["ninja_exe"] == "/usr/bin/ninja"


def test_write_tool_sets_a_top_level_key(tmp_path):
    sink = ModuleSink(tmp_path, ["# test"])
    sink.write_tool({"toolchain": "intel-llvm"})
    assert read_toml(sink.target)["tool"]["toolchain"] == "intel-llvm"


def test_clear_removes_only_the_tool_table(tmp_path):
    write_module(tmp_path, "a", tmp_path)
    sink = WorkspaceSink(tmp_path)
    sink.write_paths("linux", {"ninja_exe": "n"})
    sink.clear()
    doc = read_toml(workspace_file(tmp_path))
    assert "tool" not in doc and "a" in doc["modules"]
```

- [ ] **Step 2: Run** → fails. **Step 3: Implement**: port hub's `write_platform_paths` (adding the `header` parameter) and `render_local_config`; `write_tool` delegates to `config_base.write_tool_section(target, updates, header)`; `clear` mirrors hub's `UninstallStep._remove_config` (read, drop `tool`, re-render with `write_toml_document`, or delete the file when nothing else remains). **Step 4: Run** → pass. **Step 5: Commit** `feat(provision): add config sinks for workspace and module config`.

---

### Task 9: GPU backends

**Files:**
- Create: `sushicore/provision/gpu/{backend,cuda,rocm,level_zero,registry,provisioning}.py` copied from `sushihub/setup/gpu_backends/`
- Move tests: `test_gpu_backend_registry.py`, `test_gpu_backend_specs.py`, `test_gpu_provisioning.py`, `test_windows_cuda_install.py` → `tests/provision/`

**Interfaces:**
- Consumes: Task 2 `system`, `probe`; Task 3 `windows_installer`, `compiler_identity`.
- Produces: `gpu.registry.DEFAULT_REGISTRY`, `gpu.registry.Registry`, `gpu.backend.GpuBackendSpec`, `ToolkitInstall`, `ToolkitLocator`, `PlatformLocator`, `gpu.provisioning.provision_gpu_adapters(cfg, registry, toolchain_root, builder, dry_run)`, `gpu.cuda.CUDA`, `gpu.rocm.ROCM`, `gpu.level_zero.LEVEL_ZERO` — unchanged signatures.

- [ ] **Step 1:** Copy the six files; apply the rewrite table.
- [ ] **Step 2:** Move the four test files; in each, replace hub fixtures with `recording_console` / `provision_home` and imports with `sushicore.provision.gpu.*`. Where a test monkeypatched `sushihub.setup.gpu_backends.cuda.console`, patch `sushicore.provision._output` through the `recording_console` fixture instead.
- [ ] **Step 3: Run** `python -m pytest tests/provision -q` → pass; the moved tests' count equals hub's count for those four files (paste both counts).
- [ ] **Step 4: Commit** `feat(provision): move the GPU backend registry and locators from hub`.

---

### Task 13: GPU adapter builder

**Files:**
- Create: `sushicore/provision/gpu/adapter_builder.py` from `sushihub/setup/gpu_backends/adapter_builder.py`
- Move tests: `test_adapter_builder.py` → `tests/provision/`

**Interfaces:**
- Consumes: Task 3 `stamp.record_toolchain_adapter`, `stamp.toolchain_adapter_commit`; Task 1 `home`.
- Produces: `AdapterBuilder`, `SubprocessCommandRunner` unchanged.

- [ ] **Step 1:** Copy, rewrite imports (`..toolchains` → `..toolchains.stamp`, `deps_dir()` → `home.root()`).
- [ ] **Step 2:** Move the test; point it at `provision_home`.
- [ ] **Step 3: Run** → pass. **Step 4: Commit** `feat(provision): move the GPU adapter builder from hub`.

---

### Task 10: Stock checks

**Files:**
- Create: `sushicore/provision/checks.py`
- Test: `tests/provision/test_checks.py`

**Interfaces:**
- Consumes: Task 2 `probe.binary_works`; Task 3 `stamp`; Task 4 `IDependencySource`; Task 6 `FunctionCheck`, `CheckResult`, `State`.
- Produces (each returns a `FunctionCheck`):
  - `python_check(minimum: tuple[int, int] = (3, 10))`
  - `tool_check(name: str, exe: str, group: str = "build", required: bool = True, fix: str = "")` — ok when `probe.binary_works(exe)`, detail from `<exe> --version` first line
  - `compiler_check(cfg: ProvisionConfig, fix: str = "")` — reports every one of MSVC (`VSINSTALLDIR` or `cfg.vs_vcvars` on Windows), `clang++`, `g++` it finds, `"; "`-joined, as SushiTrack's `diag.py:165-184` does
  - `python_module_check(module: str, group: str, required: bool, fix: str)`
  - `path_check(name: str, path: Path, group: str, required: bool, fix: str)`
  - `fragment_check(source: IDependencySource, platform: str, gpu: bool, fix: str)` — one row per selected dependency whose `check_cmd` exits non-zero
  - `stamp_check(root: Path)` — warns when a toolchain directory under `root` lacks `.sushi_toolchain.json`
  - `standard_checks(cfg: ProvisionConfig, fix: str) -> list[Check]` = python, cmake, ctest, ninja (when `cfg.ninja_exe` or `ninja` resolves), compiler, git (optional)

- [ ] **Step 1: Write the failing tests**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the stock doctor checks."""

from __future__ import annotations

import sys

from sushicore.provision import checks
from sushicore.provision.doctor import State


def test_python_check_passes_on_this_interpreter():
    result = checks.python_check((3, 10)).run()
    assert result.state is State.OK
    assert sys.executable in result.detail


def test_tool_check_fails_with_the_fix_for_a_missing_tool():
    result = checks.tool_check("x", "sushi-no-such-tool", fix="st setup").run()
    assert result.state is State.FAIL
    assert result.fix == "st setup"


def test_python_module_check_finds_the_stdlib():
    assert checks.python_module_check("json", "eval", True, "").run().state is State.OK


def test_missing_python_module_fails():
    result = checks.python_module_check("sushi_no_such_mod", "infer", True, "pip install x").run()
    assert result.state is State.FAIL


def test_path_check_reports_the_missing_path(tmp_path):
    result = checks.path_check("yolox", tmp_path / "nope", "infer", True, "git submodule update").run()
    assert result.state is State.FAIL and "nope" in result.detail


def test_stamp_check_warns_on_an_unstamped_toolchain(tmp_path):
    (tmp_path / "toolchains" / "llvm-sycl").mkdir(parents=True)
    assert checks.stamp_check(tmp_path).run().state is State.WARN
```

- [ ] **Step 2: Run** → fails. **Step 3: Implement.** `python_module_check` uses `importlib.util.find_spec(module) is not None` (never imports the module). **Step 4: Run** → pass. **Step 5: Commit** `feat(provision): add the stock doctor checks`.

---

### Task 11: Package managers

**Files:**
- Create: `sushicore/provision/packages/__init__.py` (re-exports every public name below), `packages/base.py` (`IPackageManager`, `_run`, `prime_sudo`, `refresh_windows_path`, GitHub release helpers `_gh_*`, `install_gpu_stack`), `packages/linux.py` (`LinuxPackageManager`, `AptManager`, `DnfManager`, `YumManager`, `PacmanManager`, `ZypperManager`), `packages/winget.py` (`WingetManager`), `packages/direct_download.py` (`DirectDownloadWindowsManager`), `packages/vcpkg.py` (`VcpkgManager`)
- Move tests: `test_vcpkg_features.py` → `tests/provision/`

**Interfaces:**
- Consumes: Task 2 `system`, `probe.binary_works`; Task 9 `gpu.registry.DEFAULT_REGISTRY`.
- Produces: every class and function hub's `package_managers.py` exposes, same names and signatures, importable from `sushicore.provision.packages`.

- [ ] **Step 1:** Split `package_managers.py` along the file list above; each class keeps its body. Where one file needs a helper from another, import it from `.base`.
- [ ] **Step 2:** `packages/__init__.py` lists every public name hub importers use. Find them with `grep -rhoE "from \.(setup\.)?package_managers import \(?[^)]*" D:/Projects/sushistack/cli --include=*.py`.
- [ ] **Step 3:** Move the test; add `tests/provision/test_packages_api.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Pins the package-manager names hub imports."""

from __future__ import annotations

from sushicore.provision import packages


def test_every_manager_is_exported():
    for name in ("IPackageManager", "AptManager", "DnfManager", "YumManager",
                 "PacmanManager", "ZypperManager", "WingetManager",
                 "DirectDownloadWindowsManager", "VcpkgManager"):
        assert hasattr(packages, name), name
```

- [ ] **Step 4: Run** → pass. **Step 5: Commit** `feat(provision): move the package managers from hub, one file per manager`.

---

### Task 12: Toolchain installers

**Files:**
- Create: `sushicore/provision/toolchains/intel_llvm.py` (`install_intel_llvm`, `_extract_tar_gz`, `_extract_tarball`, `_run_quiet`), `toolchains/adaptivecpp.py` (`ACPP_VERSION`, `ACPP_LLVM`, `LLVM_WINDOWS_VERSION`, `install_adaptivecpp`, `_confirm_timeout`, `_find_windows_sdk_rc_dir`, `_find_windows_llvm`, `_vendor_llvm_windows`, `_explain_acpp_skip`, `_acpp_deps_linux`, `_acpp_deps_windows`), `toolchains/oneapi.py` (hub `InstallDepsStep._install_oneapi`, `_download_oneapi_installer`, `_run_oneapi_installer` as free functions `install_oneapi(ctx) -> bool`, `download_oneapi_installer() -> Path | None`, `run_oneapi_installer(installer: Path) -> bool`)
- Move tests: the installer tests left in hub's `test_toolchains.py` → `tests/provision/test_toolchain_installers.py`

**Interfaces:**
- Consumes: Task 3 `stamp`, Task 11 `packages`, Task 14 `InstallContext`.
- Produces: `install_intel_llvm(cfg, dry_run: bool, refresh: bool = False) -> Path | None`, `install_adaptivecpp(cfg, mgr, vcpkg, dry_run, assume_yes) -> str | None`, `install_oneapi(ctx: InstallContext) -> bool`.
- `_run_quiet` is needed by both installers, so it lives once in `toolchains/_process.py`.

- [ ] **Step 1:** Copy per the list; create `toolchains/_process.py` with `_run_quiet`; rewrite imports; `ctx.oneapi` → `ctx.selection.oneapi`.
- [ ] **Step 2:** Move the tests; `provision_home` replaces hub's deps-dir monkeypatch.
- [ ] **Step 3: Run** → pass. **Step 4: Commit** `feat(provision): move the intel/llvm, AdaptiveCpp and oneAPI installers from hub`.

---

### Task 15: Shared steps

**Files:**
- Create: `sushicore/provision/steps.py` from `sushihub/setup/steps.py`: `provision_adapters_for_run`, `_resolve_gpu_vendor`, `_check_cmd_ok`, `_dep_installed`, `_first_available`, `_status`, `_literal`, `_dedup`, `DetectStep` (without `_effective_required`, `_missing_requirements`, `_report_readiness`), `InstallDepsStep` (without the three oneAPI methods, which Task 12 moved), `ConfigureStep`, `UninstallStep`. **Not** moved: `VerifyStep`.
- Move tests: `test_detect_rows.py`, `test_doctor_table.py` if they import only moved symbols; otherwise they stay in hub.

**Interfaces:**
- Consumes: Tasks 2, 4, 8, 9, 11, 12, 13, 14.
- Produces:
  - `DetectStep(source: IDependencySource, managers: list[IPackageManager], after_inventory: Callable[[InstallContext, list[Dependency]], None] | None = None)` — `run` calls `after_inventory(ctx, all_deps)` where hub called `self._report_readiness(ctx, all_deps)`.
  - `InstallDepsStep(source, managers)` — calls `oneapi.install_oneapi(ctx)` where it called `self._install_oneapi(ctx)`.
  - `ConfigureStep(sink: ConfigSink)` — writes `sink.write_paths(ctx.cfg.platform, values)` where hub called `probe.write_platform_paths(workspace_file(), …)`, and `sink.write_tool({"toolchain": ctx.active_toolchain})` where hub called `set_toolchain(ctx.active_toolchain)`.
  - `UninstallStep(source, managers, sink: ConfigSink)` — `_remove_config` becomes `self._sink.clear()`.

- [ ] **Step 1: Write the failing test** `tests/provision/test_steps.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the seams the shared steps gained."""

from __future__ import annotations

from sushicore.provision import probe, steps
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.pipeline import InstallContext, StepResult


class _Sink:
    def __init__(self):
        self.paths, self.tool = [], []

    def write_paths(self, platform, values):
        self.paths.append((platform, values))

    def write_tool(self, updates):
        self.tool.append(updates)


def test_configure_writes_through_the_sink(monkeypatch, recording_console):
    monkeypatch.setattr(probe, "resolve_local_config", lambda cfg, gpu=False: {"ninja_exe": "n"})
    sink = _Sink()
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"), active_toolchain="intel-llvm")
    assert steps.ConfigureStep(sink).run(ctx) is StepResult.OK
    assert sink.paths == [("linux", {"ninja_exe": "n"})]
    assert sink.tool == [{"toolchain": "intel-llvm"}]
```

- [ ] **Step 2: Run** → fails. **Step 3: Implement** per the interface list. **Step 4: Run** `python -m pytest -q` → pass. **Step 5: Commit** `feat(provision): move the shared install steps from hub behind sinks and hooks`.

---

### Task 16: Module commands

**Files:**
- Create: `sushicore/provision/commands.py`
- Test: `tests/provision/test_commands.py`

**Interfaces:**
- Consumes: Tasks 4, 6, 7, 8, 10, 14, 15, `sushicore.profile.ModuleProfile`.
- Produces:

```python
@dataclass(frozen=True)
class ModuleProvision:
    """What one module CLI hands the shared commands."""

    profile: ModuleProfile
    project_root: Callable[[], Path]
    load_config: Callable[[], ProvisionConfig]
    console: Callable[[], object]
    extra_checks: Callable[[], list[Check]] = lambda: []
    fragment: str = "cli/sushistack.deps.toml"


def register_provision_commands(app: typer.Typer, module: ModuleProvision) -> None:
    """Add ``setup``, ``doctor``, ``link`` and ``unlink`` to *app*."""
```

  - `setup [--dry-run] [--yes]`: binds `module.console`, takes `ProvisionLock(home.root() / ".lock")`, builds `TomlDependencySource([(root / module.fragment, module.profile.name)])`, runs `DetectStep → InstallDepsStep → ConfigureStep(ModuleSink(root / "cli", header))` with `consumer=module.profile.name` and an empty `ToolchainSelection`, then runs `doctor`. Exit code: 1 when the pipeline fails or doctor reports failures.
  - `doctor [--for GROUP]`: `Doctor(standard_checks(cfg, fix=f"{program} setup") + module.extra_checks()).run(groups)`; renders; exits with `report.exit_code()`.
  - `link [--workspace PATH]`: workspace = `--workspace`, else `SUSHISTACK_HOME`, else walk up for `.sushistack` from the project root; none found → error naming both ways to supply it, exit 2. Writes `write_module(workspace, profile.name, project_root)`.
  - `unlink [--workspace PATH]`: `remove_module`; prints whether anything was removed; exit 0 either way.

- [ ] **Step 1: Write the failing tests**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the setup/doctor/link/unlink commands."""

from __future__ import annotations

import typer
from typer.testing import CliRunner

from sushicore.profile import ModuleProfile
from sushicore.provision.commands import ModuleProvision, register_provision_commands
from sushicore.provision.config import ProvisionSettings
from sushicore.workspace import registered_modules


def _app(tmp_path, recording_console):
    profile = ModuleProfile(name="sushidsp", program="sd", env_prefix="SD",
                            root_marker="sushidsp.marker")
    app = typer.Typer()

    @app.callback()
    def _root():
        """Test app."""

    register_provision_commands(app, ModuleProvision(
        profile=profile, project_root=lambda: tmp_path / "dsp",
        load_config=lambda: ProvisionSettings(platform="linux"),
        console=lambda: recording_console))
    return app


def test_link_and_unlink_without_hub(tmp_path, recording_console):
    ws = tmp_path / "ws"
    (ws / ".sushistack").mkdir(parents=True)
    app = _app(tmp_path, recording_console)
    runner = CliRunner()
    assert runner.invoke(app, ["link", "--workspace", str(ws)]).exit_code == 0
    assert registered_modules(ws) == {"sushidsp": str(tmp_path / "dsp")}
    assert runner.invoke(app, ["unlink", "--workspace", str(ws)]).exit_code == 0
    assert registered_modules(ws) == {}


def test_link_outside_a_workspace_exits_two(tmp_path, recording_console, monkeypatch):
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(_app(tmp_path, recording_console), ["link"])
    assert result.exit_code == 2


def test_doctor_filters_by_group(tmp_path, recording_console):
    result = CliRunner().invoke(_app(tmp_path, recording_console), ["doctor", "--for", "infer"])
    assert result.exit_code == 0
```

Read `ModuleProfile`'s real constructor before writing the fixture; match its required fields.

- [ ] **Step 2: Run** → fails. **Step 3: Implement.** `typer` is imported inside `register_provision_commands` so sushicore keeps working without the `typer` extra. **Step 4: Run** → pass. **Step 5: Commit** `feat(provision): add setup, doctor, link and unlink for module CLIs`.

---

### Task 17: Layering guard

**Files:**
- Create: `tests/provision/test_layering.py`

- [ ] **Step 1: Write the test**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Keeps provision's layers pointing downward and free of hub."""

from __future__ import annotations

import ast
from pathlib import Path

import sushicore.provision as provision

_ROOT = Path(provision.__file__).parent
_LAYER = {
    "_output": 0, "config": 0, "home": 0,
    "system": 1, "probe": 1, "toolchains.stamp": 1, "gpu.compiler_identity": 1,
    "gpu.windows_installer": 1, "fragments": 1, "registry": 1, "lock": 1, "doctor": 1,
    "pipeline": 1, "sinks": 2, "gpu.backend": 2, "gpu.cuda": 2, "gpu.rocm": 2,
    "gpu.level_zero": 2, "gpu.registry": 2, "gpu.provisioning": 2, "gpu.adapter_builder": 2,
    "checks": 2, "packages": 3, "toolchains.intel_llvm": 4, "toolchains.adaptivecpp": 4,
    "toolchains.oneapi": 4, "toolchains._process": 1, "steps": 5, "commands": 6,
}


def _module_name(path: Path) -> str:
    rel = path.relative_to(_ROOT).with_suffix("")
    parts = [p for p in rel.parts if p != "__init__"]
    if parts and parts[0] == "packages":
        return "packages"
    return ".".join(parts)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(("." * node.level) + node.module)
        elif isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
    return names


def test_no_module_imports_hub():
    for path in _ROOT.rglob("*.py"):
        assert not any("sushihub" in n for n in _imports(path)), path


def test_every_module_has_a_layer():
    for path in _ROOT.rglob("*.py"):
        name = _module_name(path)
        if name:
            assert name in _LAYER, name


def _resolve(path: Path, imported: str) -> str | None:
    """Return the provision module a relative import names, or None for other imports."""
    level = len(imported) - len(imported.lstrip("."))
    if level == 0:
        prefix = "sushicore.provision."
        return imported[len(prefix):] if imported.startswith(prefix) else None
    base = list(path.relative_to(_ROOT).with_suffix("").parts[:-1])
    base = base[:len(base) - (level - 1)] if level > 1 else base
    target = [*base, *[p for p in imported.lstrip(".").split(".") if p]]
    if target and target[0] == "packages":
        return "packages"
    name = ".".join(target)
    return name if name in _LAYER else None


def test_imports_point_down_or_sideways():
    for path in _ROOT.rglob("*.py"):
        own = _module_name(path)
        if not own:
            continue
        for imported in _imports(path):
            target = _resolve(path, imported)
            if target and target != own:
                assert _LAYER[target] <= _LAYER[own], f"{own} imports {target}"
```

- [ ] **Step 2: Run** → pass (fix any unlisted module by assigning its layer, not by deleting the assertion).
- [ ] **Step 3: Commit** `test(provision): guard the layering and the hub boundary`.

---

### Task 18: Version, README and changelog

**Files:**
- Modify: `pyproject.toml` (`version = "0.5.0"`, description adds "dependency provisioning and doctor"), `README.md` (new `## Provisioning` section: the root, the four commands, `bind_console`/`bind_root`, a 10-line module example using `ModuleProvision`), `docs/reference/CHANGELOG.md` (one line, spec's style)

- [ ] **Step 1:** Edit the three files. The changelog line:

`- 2026-09-23 — Added `sushicore.provision`: dependency root, registry, doctor and module commands, moved from hub (`sushicore/provision/`).`

- [ ] **Step 2: Run** `python -m pytest -q` in sushicore and, with `PYTHONPATH=D:/Projects/sushicore`, `python -m pytest -q` in `D:/Projects/sushistack/cli`. Expected: both pass; hub unchanged so far.
- [ ] **Step 3: Commit** `chore(release): prepare sushicore 0.5.0`. Do not tag, do not publish.

---

### Task 19: Owner gate — give hub's venv the new sushicore

**Stop and ask the owner before any command in this task.** Show them the commands and wait.

- [ ] **Step 1:** Record the current state: `pipx runpip sushihub show sushicore` (expect 0.4.0) and `hub doctor` output.
- [ ] **Step 2:** `pipx runpip sushihub install -e D:\Projects\sushicore`
- [ ] **Step 3:** `hub --help` and `hub doctor`. Expected: identical to Step 1 apart from the version line. If anything differs, roll back with `pipx runpip sushihub install sushicore==0.4.0` and stop.

---

### Task 20: Hub re-exports — probe, system, stamp, GPU

**Files (sushistack):**
- Modify: `cli/sushihub/setup/apt.py`, `setup/probe.py`, `setup/gpu_backends/*.py` (every file), `cli/sushihub/__init__.py` or the CLI callback in `cli/sushihub/cli.py` — **only** to add the two bind calls below
- Delete: hub tests moved in Tasks 2, 3, 9, 13

**Interfaces:** each module becomes the re-export shape above. `probe.py` keeps `write_platform_paths` and `render_local_config` as re-exports from `sushicore.provision.sinks`, wrapped so the old signature (no `header`) still works:

```python
from sushicore.provision.sinks import render_local_config  # noqa: F401
from sushicore.provision.sinks import write_platform_paths as _write

from ..config import WORKSPACE_HEADER


def write_platform_paths(target, platform, values):
    """Write ``[tool.<platform>]`` into *target* under hub's workspace header."""
    return _write(target, platform, values, WORKSPACE_HEADER)
```

Bind calls, placed where hub's CLI starts (the Typer root callback), so the root stays hub's until sub-project 2:

```python
from sushicore import provision
from sushicore.provision import home

from . import console
from .config import deps_dir

provision.bind_console(console.current)
home.bind_root(deps_dir)
```

- [ ] **Step 1:** Replace the modules; add the bind calls.
- [ ] **Step 2: Run** `PYTHONPATH=D:/Projects/sushicore python -m pytest -q` in `sushistack/cli`. The test interpreter is not hub's pipx venv, so the path points it at the same sushicore Task 19 installed. Expected: pass.
- [ ] **Step 3:** `hub doctor`. Expected: same output as Task 19 Step 3.
- [ ] **Step 4: Commit** (sushistack) `refactor(setup): take probing, stamps and GPU backends from sushicore`.

### Task 21: Hub re-exports — fragments, packages, toolchains

**Files (sushistack):** `setup/dependency_source.py` (keeps the hub-only discovery functions, re-exports the rest; `TomlDependencySource()` with no argument keeps working through a hub subclass that passes `manifest_sources()`), `setup/ordering.py`, `setup/package_managers.py`, `setup/toolchains.py`; delete hub tests moved in Tasks 4, 11, 12.

```python
class TomlDependencySource(_CoreSource):
    """Hub's source: the core source fed the workspace-wide manifest list."""

    def __init__(self, sources=None) -> None:
        """Default to every manifest the workspace carries."""
        super().__init__(manifest_sources() if sources is None else sources)
```

- [ ] Steps: replace, run hub tests with `PYTHONPATH=D:/Projects/sushicore`, `hub doctor`, commit `refactor(setup): take fragments, package managers and installers from sushicore`.

### Task 22: Hub re-exports — pipeline, steps, links, factory

**Files (sushistack):** `setup/pipeline.py`, `setup/selection.py` (keeps `MACHINE_COMPONENTS`, `components` as a function `components(selection)`, `selection_from_source`; re-exports `ToolchainSelection`), `setup/steps.py` (re-exports; keeps `VerifyStep` and moves `_effective_required`, `_missing_requirements`, `_report_readiness` into a hub function `report_readiness(ctx, all_deps)`), `setup/factory.py` (builds `InstallContext(cfg=…, selection=ToolchainSelection(**sel), consumer="sushistack", …)`, `DetectStep(source, managers, after_inventory=report_readiness)`, `ConfigureStep(WorkspaceSink(workspace_root()))`, `UninstallStep(source, managers, WorkspaceSink(workspace_root()))`), `services/links.py` (delegates to `sushicore.workspace.registered_modules`/`write_module` with `workspace_root()`), `services/setup.py:43` (`ctx.install_acpp` → `ctx.selection.install_acpp`), `services/customize.py` if it reads the context fields.

- [ ] Steps: replace, run hub tests with `PYTHONPATH=D:/Projects/sushicore`, then `hub doctor`, `hub install --dry-run` (compare with the Task 19 baseline and paste both), commit `refactor(setup): run hub's install through sushicore.provision`.
- [ ] Final step: `hub` changelog line and `cli/pyproject.toml` `sushicore>=0.5.0`, commit `build(cli): require sushicore 0.5.0`. Tell the owner that reinstalling hub now needs sushicore 0.5.0 published or installed editable.
