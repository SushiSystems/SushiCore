# Standalone provisioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `sr`, `sb`, `sa` and `se` gain `setup`, `doctor`, `link` and `unlink` from `sushicore.provision`, so every module builds after one command without hub, and hub reads the same rules from sushicore.

**Architecture:** sushicore gains four bricks: a toolchain selection rule, a `depends_on` closure, the shared base fragment, and a probe that reads every dependency root. `register_provision_commands` grows to carry them. Each module CLI then registers the commands with one call and deletes its own dependency-root code. Hub deletes its copy of the selection rule and the base fragment and reads sushicore's.

**Tech Stack:** Python 3.10+, Typer, pytest, `tomllib`, `sushicore` installed editable from `D:/Projects/sushicore`.

**Spec:** `D:/Projects/sushicore/docs/agent/specs/2026-10-04-standalone-provision-design.md`

## Global Constraints

- Owner decisions, 2026-10-04: the plan runs in waves; sushicore 0.7.0 is tagged and published only after every wave has landed and the owner has run the real commands.
- Nothing on the owner's machine breaks. Every CLI runs live from its working tree, so every commit leaves every CLI importable. A sushicore change that removes a name lands only after its last caller stopped using it.
- `sushicore` becomes `0.7.0`. Every module CLI and hub require `sushicore>=0.7.0`.
- Nobody runs a build: no `sr build`, `sb build`, `sa build`, `se build`, `sd build`, `st build`, cmake, ninja or ctest. No build configuration file is edited. Evidence is pytest, `setup --dry-run` and `doctor`.
- No real `setup` without `--dry-run`. The owner runs the real ones in wave 4.
- Stage by path. Never `git add -A`. `D:/Projects/sushiengine` has 372 uncommitted files outside `cli/`; nothing outside `cli/`, `docs/reference/CHANGELOG.md` and the README section this plan names is touched there, and a file already dirty is reported, not edited.
- Subagents never commit, stash, checkout, reset or create worktrees. The controller commits per task, by path.
- Python files open with the repository's licence header where its siblings carry one, then a module docstring. Every function has a Google-style docstring whose summary is one sentence starting with a verb.
- Changelog line: `- 2026-10-04 — <scope>: <Past-tense verb> <what> (`paths`).` One sentence, at most 240 characters, no reason.
- Commit subjects follow `type(scope): sentence`, under 72 characters.
- Hub's dependency tree does not move in this plan.

## Review Focus

1. A machine whose toolchains sit in the legacy `<workspace>/dependencies` tree and not in `~/.sushisystems`: `sr setup --dry-run` reports intel-llvm as present and selects no download. (Task 2 and Task 4 tests.)
2. `sb setup` with no `../sushiruntime`: exit code 2, one line naming `sushiruntime` and the path looked at, nothing written, no package manager called. (Task 7 test.)
3. `sr setup --toolchain typo`: exit code 2 naming the valid keys, before the lock is taken. (Task 7 test.)
4. A workspace whose `[modules]` holds `SushiDSP = "..."` from the old `sd link`: `sd unlink` removes it, and `sd link` writes `sushidsp`. (Task 1 test.)
5. `se --help` run outside any engine checkout: the four commands are listed and nothing raises. (Task 13 test.)

## Waves

| Wave | Tasks | Repository and files | Waits on | Controller build after |
| --- | --- | --- | --- | --- |
| 0 | Task 0 (owner) | pipx environments | nothing | `sr --help`, `sb --help`, `sa --help`, `se --help` |
| 1 | Tasks 1 to 9, serial, controller | sushicore | Task 0 | sushicore, hub, sd and st pytest |
| 2 | Tasks 10 ∥ 11 ∥ 12 ∥ 13 ∥ 14 ∥ 15, one subagent each (opus, low), then one reviewer each (opus, medium) | sushiruntime ∥ sushiblas ∥ sushiai ∥ sushiengine ∥ sushidsp ∥ sushitrack, each its own `cli/` | Wave 1 | each module's pytest, `setup --dry-run`, `doctor` |
| 3 | Task 16, controller | sushistack `cli/`, `docs/` | Wave 1 | hub pytest, `hub install --dry-run`, `hub doctor` |
| 4 | Task 17 (owner) | real `setup`, builds, tag, publish | Waves 2 and 3 | every module's build |

---

### Task 0: Owner gate — editable sushicore under every module CLI

`pipx list --short` on 2026-10-04 shows `sushiai-cli`, `sushiblas-cli`, `sushidsp-cli`, `sushiengine-cli`, `sushihub` and `sushiruntime-cli`. `st` is installed with pip.

- [ ] **Step 1:** The controller runs, for each of the six, `pipx runpip <package> show sushicore` and reads `Editable project location`.
- [ ] **Step 2:** For each that does not name `D:\Projects\sushicore`, the owner runs `pipx runpip <package> install -e D:\Projects\sushicore`.

Acceptance: all six report the editable location and `sr --help`, `sb --help`, `sa --help`, `se --help` open.

---

### Task 1: A module's registry key

**Files:**
- Modify: `D:/Projects/sushicore/sushicore/profile.py`
- Modify: `D:/Projects/sushicore/sushicore/provision/commands.py`
- Test: `D:/Projects/sushicore/tests/test_profile.py`, `D:/Projects/sushicore/tests/provision/test_commands.py`

**Interfaces:**
- Produces: `ModuleProfile.key -> str`, the lower-cased `name`. It is the owner of the module's fragment, the registry consumer, and its name in a workspace's `[modules]`.

`profile.name` is the display name (`SushiDSP`). `commands.py` uses it as the fragment owner and as the `[modules]` key, so `sd link` writes `SushiDSP` where `hub link` writes `sushidsp`, and `DetectStep` never matches the owner `sushiruntime`.

- [ ] **Step 1: Failing tests.** Append to `tests/test_profile.py`:

```python
def test_key_is_the_lower_cased_name():
    """Check that key is the lower cased name."""
    assert ModuleProfile(name="SushiDSP", program="sd", env_prefix="SD").key == "sushidsp"
```

Append to `tests/provision/test_commands.py`:

```python
def _mixed_case_app(tmp_path, recording_console):
    """Return an app whose profile carries a display name in mixed case."""
    profile = ModuleProfile(name="SushiDSP", program="sd", env_prefix="SD",
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


def test_link_records_the_lower_cased_key(tmp_path, recording_console):
    """Check that link records the lower cased key."""
    ws = tmp_path / "ws"
    (ws / ".sushistack").mkdir(parents=True)
    (tmp_path / "dsp" / "cli").mkdir(parents=True)
    app = _mixed_case_app(tmp_path, recording_console)
    assert CliRunner().invoke(app, ["link", "--workspace", str(ws)]).exit_code == 0
    assert list(registered_modules(ws)) == ["sushidsp"]


def test_unlink_removes_an_entry_written_under_the_display_name(tmp_path, recording_console):
    """Check that unlink removes an entry written under the display name."""
    ws = tmp_path / "ws"
    (ws / ".sushistack").mkdir(parents=True)
    (tmp_path / "dsp" / "cli").mkdir(parents=True)
    write_module(ws, "SushiDSP", tmp_path / "dsp")
    app = _mixed_case_app(tmp_path, recording_console)
    assert CliRunner().invoke(app, ["unlink", "--workspace", str(ws)]).exit_code == 0
    assert registered_modules(ws) == {}
```

Add `write_module` to that file's `sushicore.workspace` import.

- [ ] **Step 2: Run** `cd D:/Projects/sushicore && python -m pytest tests/test_profile.py tests/provision/test_commands.py -q`. Expected: FAIL, `ModuleProfile` has no `key`.

- [ ] **Step 3: Implement.** In `profile.py`, after `env_tokens`:

```python
    @property
    def key(self) -> str:
        """Return the lower-cased name this module is recorded under."""
        return self.name.lower()
```

In `commands.py`: `_module_source` passes `module.profile.key` as the owner; `InstallContext(consumer=module.profile.key, ...)`; `link` calls `write_module(target, module.profile.key, root)`; `unlink` removes both spellings and reports one result:

```python
        removed = [remove_module(target, name)
                   for name in dict.fromkeys((module.profile.key, module.profile.name))]
        if any(removed):
```

Messages keep `module.profile.name`.

- [ ] **Step 4: Run** the sushicore suite. Changelog: `- 2026-10-04 — provision: Recorded a module under its lower-cased key in fragments, the registry and a workspace's module list (`sushicore/profile.py`, `sushicore/provision/commands.py`).`

Acceptance: sushicore suite green (747 plus the three new tests).

---

### Task 2: The probe reads every dependency root

**Files:**
- Modify: `D:/Projects/sushicore/sushicore/provision/probe.py` (`_toolchains_dir`, `_discover_installed_toolchains`, `toolchain_status`, the vcpkg default in `_resolve_windows`)
- Test: `D:/Projects/sushicore/tests/provision/test_probe.py`

**Interfaces:**
- Consumes: `home.search_roots() -> list[Path]`.
- Produces: `probe.installed_toolchain(name: str, relative: Path) -> Path | None`, the first `<root>/toolchains/<name>/<relative>` that is a file, across `home.search_roots()` in order.

Today the probe looks under `home.root()` alone. The 2026-09-23 spec promised that a component present in a legacy tree counts as installed; the probe never did that.

- [ ] **Step 1: Failing tests** appended to `tests/provision/test_probe.py` (read its fixtures first; use `provision_home` from `conftest.py`):

```python
def test_installed_toolchain_prefers_the_current_root(provision_home, tmp_path, monkeypatch):
    """Check that installed toolchain prefers the current root."""
    legacy = tmp_path / "legacy"
    monkeypatch.setenv("SUSHISTACK_DEPS_DIR", str(legacy))
    for root in (provision_home, legacy):
        (root / "toolchains" / "llvm-sycl" / "bin").mkdir(parents=True)
        (root / "toolchains" / "llvm-sycl" / "bin" / "clang++").write_text("")
    found = probe.installed_toolchain("llvm-sycl", Path("bin") / "clang++")
    assert found == provision_home / "toolchains" / "llvm-sycl" / "bin" / "clang++"


def test_installed_toolchain_falls_back_to_a_legacy_root(provision_home, tmp_path, monkeypatch):
    """Check that installed toolchain falls back to a legacy root."""
    legacy = tmp_path / "legacy"
    monkeypatch.setenv("SUSHISTACK_DEPS_DIR", str(legacy))
    exe = legacy / "toolchains" / "llvm-sycl" / "bin" / "clang++"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    assert probe.installed_toolchain("llvm-sycl", Path("bin") / "clang++") == exe


def test_installed_toolchain_is_none_when_no_root_holds_it(provision_home):
    """Check that installed toolchain is none when no root holds it."""
    assert probe.installed_toolchain("llvm-sycl", Path("bin") / "clang++") is None


def test_discovery_records_a_legacy_bundle(provision_home, tmp_path, monkeypatch):
    """Check that discovery records a legacy bundle."""
    legacy = tmp_path / "legacy"
    monkeypatch.setenv("SUSHISTACK_DEPS_DIR", str(legacy))
    exe = legacy / "toolchains" / "llvm-sycl" / "bin" / "clang++"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    values: dict[str, str] = {}
    probe._discover_installed_toolchains(ProvisionSettings(platform="linux"), values)
    assert values["llvm_root"] == str(legacy / "toolchains" / "llvm-sycl")
```

Import `Path` and `ProvisionSettings` if the file does not.

- [ ] **Step 2: Run** `python -m pytest tests/provision/test_probe.py -q`. Expected: FAIL, no `installed_toolchain`.

- [ ] **Step 3: Implement.** Add:

```python
def installed_toolchain(name: str, relative: Path) -> Path | None:
    """Return the first ``toolchains/<name>/<relative>`` file across the dependency roots."""
    for root in home.search_roots():
        candidate = root / "toolchains" / name / relative
        if candidate.is_file():
            return candidate
    return None
```

`_discover_installed_toolchains` and `toolchain_status` resolve clang++ through `installed_toolchain("llvm-sycl", Path("bin") / exe)` and acpp through `installed_toolchain("adaptivecpp", Path("bin") / name)` for `acpp.bat` then `acpp`; `llvm_root` is the found file's `parents[1]`. In `_resolve_windows`, the vcpkg default becomes the first `root / "vcpkg"` that is a directory across `home.search_roots()`, else `home.root() / "vcpkg"` as today. `_toolchains_dir` stays for the installers, which write to the current root.

- [ ] **Step 4: Run** the sushicore suite, then hub's (`cd D:/Projects/sushistack/cli && python -m pytest -q`). Hub binds the root to its own tree, so its output is unchanged. Changelog: `- 2026-10-04 — provision: Made the probe find toolchains and vcpkg in every dependency root, the legacy trees included (`sushicore/provision/probe.py`).`

Acceptance: both suites green.

---

### Task 3: The base fragment ships in sushicore

**Files:**
- Create: `D:/Projects/sushicore/sushicore/provision/manifests/__init__.py`
- Create: `D:/Projects/sushicore/sushicore/provision/manifests/base.deps.toml` (a byte copy of `D:/Projects/sushistack/cli/sushihub/manifests/base.deps.toml`, with its header comment's `hub`-specific sentences rewritten to name `setup` and `hub install` both)
- Modify: `D:/Projects/sushicore/pyproject.toml` (`[tool.setuptools.package-data] sushicore = ["py.typed", "provision/manifests/*.deps.toml"]`)
- Modify: `D:/Projects/sushicore/tests/provision/test_layering.py` (`"manifests": 0` in `_LAYER`)
- Test: `D:/Projects/sushicore/tests/provision/test_manifests.py`

**Interfaces:**
- Produces: `sushicore.provision.manifests.base_fragment() -> Path`; `sushicore.provision.manifests.BASE_OWNER = "shared"`, equal to `fragments.SHARED_OWNER`.

Hub keeps its own copy until Task 16 deletes it, so nothing breaks in between.

- [ ] **Step 1: Failing test:**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the shared base fragment."""

from __future__ import annotations

from sushicore import deps_fragment
from sushicore.provision import fragments, manifests


def test_base_fragment_is_a_readable_file():
    """Check that base fragment is a readable file."""
    names = {dep.name for dep in deps_fragment.read(manifests.base_fragment()).dependencies}
    assert {"cmake", "ninja", "gtest", "opencl", "pkgconf", "build_tools"} <= names


def test_base_fragment_declares_no_module_dependency():
    """Check that base fragment declares no module dependency."""
    assert deps_fragment.read(manifests.base_fragment()).depends_on == []


def test_base_owner_is_the_shared_owner():
    """Check that base owner is the shared owner."""
    assert manifests.BASE_OWNER == fragments.SHARED_OWNER
```

- [ ] **Step 2: Run** `python -m pytest tests/provision/test_manifests.py -q`. Expected: FAIL, no module.

- [ ] **Step 3: Implement** `manifests/__init__.py`:

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The dependency fragment every SYCL module shares."""

from __future__ import annotations

from pathlib import Path

#: Owner label carried by the dependencies the base fragment declares.
BASE_OWNER = "shared"


def base_fragment() -> Path:
    """Return the path of the base fragment shipped in this package."""
    return Path(__file__).with_name("base.deps.toml")
```

Copy the fragment. `BASE_OWNER` is a literal so this layer-0 module imports nothing; the third test pins it to `SHARED_OWNER`.

- [ ] **Step 4: Run** the sushicore suite. Changelog: `- 2026-10-04 — provision: Added the shared base dependency fragment, moved from hub (`sushicore/provision/manifests/`).`

Acceptance: suite green, and `python -c "from sushicore.provision.manifests import base_fragment; print(base_fragment().is_file())"` prints `True`.

---

### Task 4: The toolchain selection rule

**Files:**
- Create: `D:/Projects/sushicore/sushicore/provision/selection.py`
- Modify: `D:/Projects/sushicore/tests/provision/test_layering.py` (`"selection": 2`)
- Test: `D:/Projects/sushicore/tests/provision/test_selection.py`

**Interfaces:**
- Consumes: `IDependencySource.all()`, `ToolchainSelection`.
- Produces:
  - `Component(key: str, label: str, field: str)`, frozen.
  - `COMPONENTS: tuple[Component, ...]`, the four rows hub's `CUSTOMIZABLE_COMPONENTS` holds today, same order and labels.
  - `GPU_KEY = "gpu"`.
  - `toolchain_keys() -> tuple[str, ...]`: every key but `GPU_KEY`.
  - `groups(source: IDependencySource) -> dict[str, list[str]]`: the declared toolchain keys by capability, both in declaration order.
  - `derive(source: IDependencySource, present: Mapping[str, bool], *, requested: Sequence[str] = (), gpu: bool = True) -> ToolchainSelection`. Raises `ValueError` naming the valid keys when `requested` holds an unknown one.

The rule: declared toolchain components are grouped by their `provides` tag, a component with none forming a group of its own. A group with a present member turns nothing on. Otherwise its first declared member turns on. Each requested key turns on. The GPU component turns on when `gpu` is true and some declared dependency is `gpu_only`.

- [ ] **Step 1: Failing tests:**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the toolchain selection rule."""

from __future__ import annotations

import pytest

from sushicore.provision.fragments import Dependency, IDependencySource
from sushicore.provision.selection import COMPONENTS, derive, toolchain_keys


class _Source(IDependencySource):
    """A dependency source holding a fixed list."""

    def __init__(self, deps: list[Dependency]) -> None:
        """Hold *deps* as the declared dependencies."""
        self._deps = deps

    def all(self) -> list[Dependency]:
        """Return the fixed list."""
        return list(self._deps)


def _sycl(name: str) -> Dependency:
    """Return a toolchain dependency providing the SYCL capability."""
    return Dependency(name=name, provides="sycl-toolchain", owner="sushiruntime")


_RUNTIME = _Source([_sycl("intel-llvm"), _sycl("adaptivecpp"), _sycl("oneapi")])


def test_an_unsatisfied_group_turns_on_its_first_declared_member():
    """Check that an unsatisfied group turns on its first declared member."""
    selection = derive(_RUNTIME, present={})
    assert (selection.install_intel_llvm, selection.install_acpp, selection.oneapi) == (
        True, False, False)


def test_declaration_order_decides_the_default():
    """Check that declaration order decides the default."""
    source = _Source([_sycl("adaptivecpp"), _sycl("intel-llvm")])
    selection = derive(source, present={})
    assert (selection.install_acpp, selection.install_intel_llvm) == (True, False)


def test_a_satisfied_group_turns_nothing_on():
    """Check that a satisfied group turns nothing on."""
    selection = derive(_RUNTIME, present={"oneapi": True})
    assert not (selection.install_intel_llvm or selection.install_acpp or selection.oneapi)


def test_a_requested_key_turns_on_beside_the_default():
    """Check that a requested key turns on beside the default."""
    selection = derive(_RUNTIME, present={}, requested=["adaptivecpp"])
    assert (selection.install_intel_llvm, selection.install_acpp) == (True, True)


def test_a_requested_key_turns_on_in_a_satisfied_group():
    """Check that a requested key turns on in a satisfied group."""
    selection = derive(_RUNTIME, present={"intel-llvm": True}, requested=["oneapi"])
    assert (selection.install_intel_llvm, selection.oneapi) == (False, True)


def test_an_unknown_requested_key_raises_and_names_the_valid_ones():
    """Check that an unknown requested key raises and names the valid ones."""
    with pytest.raises(ValueError) as error:
        derive(_RUNTIME, present={}, requested=["typo"])
    assert all(key in str(error.value) for key in toolchain_keys())


def test_a_source_declaring_no_toolchain_selects_none():
    """Check that a source declaring no toolchain selects none."""
    selection = derive(_Source([Dependency(name="sdl2", owner="sushidsp")]), present={})
    assert not (selection.install_intel_llvm or selection.install_acpp or selection.oneapi)


def test_gpu_is_passed_through():
    """Check that gpu is passed through."""
    assert derive(_RUNTIME, present={}).gpu is True
    assert derive(_RUNTIME, present={}, gpu=False).gpu is False


def test_the_component_table_names_every_selection_field():
    """Check that the component table names every selection field."""
    assert [c.field for c in COMPONENTS] == [
        "install_intel_llvm", "install_acpp", "oneapi", "gpu"]
```

If `Dependency` requires fields beyond `name`, read `sushicore/deps_fragment.py` and pass its defaults.

- [ ] **Step 2: Run** `python -m pytest tests/provision/test_selection.py -q`. Expected: FAIL, no module.

- [ ] **Step 3: Implement:**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Decides which toolchain components one provisioning run installs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .fragments import IDependencySource
from .pipeline import ToolchainSelection


@dataclass(frozen=True)
class Component:
    """One heavy component a run can install, and the selection field it sets."""

    key: str
    label: str
    field: str


#: Key of the component that follows the machine, not a fragment.
GPU_KEY = "gpu"

COMPONENTS: tuple[Component, ...] = (
    Component("intel-llvm", "intel/llvm SYCL toolchain (clang++ -fsycl) — primary",
              "install_intel_llvm"),
    Component("adaptivecpp", "AdaptiveCpp (acpp) — secondary SYCL toolchain", "install_acpp"),
    Component("oneapi", "Intel oneAPI DPC++ (icx/icpx) — heavy, several GB", "oneapi"),
    Component(GPU_KEY, "Toolkit for this machine's GPU, detected automatically", "gpu"),
)

_FIELD = {component.key: component.field for component in COMPONENTS}


def toolchain_keys() -> tuple[str, ...]:
    """Return the key of every component a fragment can declare."""
    return tuple(component.key for component in COMPONENTS if component.key != GPU_KEY)


def groups(source: IDependencySource) -> list[list[str]]:
    """Return the declared toolchain keys grouped by capability, in declaration order."""
    groups: dict[str, list[str]] = {}
    for dep in source.all():
        if dep.name in toolchain_keys():
            groups.setdefault(dep.provides or dep.name, []).append(dep.name)
    return list(groups.values())


def derive(source: IDependencySource, present: Mapping[str, bool], *,
           requested: Sequence[str] = (), gpu: bool = True) -> ToolchainSelection:
    """Return the components to install for *source* on a machine holding *present*.

    Args:
        source: The declared dependencies.
        present: Toolchain key to whether the machine already has it.
        requested: Keys to install whatever the machine has.
        gpu: Whether the run provisions the detected GPU's toolkit.

    Raises:
        ValueError: *requested* holds a key no component carries.
    """
    unknown = [key for key in requested if key not in toolchain_keys()]
    if unknown:
        raise ValueError(
            f"Unknown toolchain '{unknown[0]}'; choose one of: {', '.join(toolchain_keys())}.")
    chosen = {members[0] for members in groups(source)
              if not any(present.get(member) for member in members)}
    chosen.update(requested)
    values = {_FIELD[key]: True for key in chosen}
    values[_FIELD[GPU_KEY]] = gpu
    return ToolchainSelection(**values)
```

- [ ] **Step 4: Run** the sushicore suite. Changelog: `- 2026-10-04 — provision: Added the toolchain selection rule and its component table, moved from hub (`sushicore/provision/selection.py`).`

Acceptance: suite green.

---

### Task 5: The dependency closure

**Files:**
- Create: `D:/Projects/sushicore/sushicore/provision/closure.py`
- Modify: `D:/Projects/sushicore/tests/provision/test_layering.py` (`"closure": 2`)
- Test: `D:/Projects/sushicore/tests/provision/test_closure.py`

**Interfaces:**
- Consumes: `deps_fragment.read(path).depends_on`.
- Produces:
  - `DEFAULT_FRAGMENT = "cli/sushistack.deps.toml"`.
  - `Locate = Callable[[str], Optional[Path]]`.
  - `Closure(sources: tuple[tuple[Path, str], ...], missing: tuple[tuple[str, str], ...])`, frozen. `missing` holds `(module, wanted by)` pairs.
  - `resolve(key: str, root: Path, locate: Locate, *, fragment: str = DEFAULT_FRAGMENT, shared: Sequence[tuple[Path, str]] = ()) -> Closure`. Raises `ValueError` on a cycle.

`sources` holds `shared` first, then each dependency before the module that names it, the module itself last. A dependency's fragment is read at `DEFAULT_FRAGMENT` under its checkout. A located checkout with no fragment is present and contributes nothing.

- [ ] **Step 1: Failing tests:**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the dependency closure."""

from __future__ import annotations

import pytest

from sushicore.provision.closure import DEFAULT_FRAGMENT, resolve


def _module(tmp_path, name, depends_on=()):
    """Create a checkout named *name* whose fragment depends on *depends_on*."""
    root = tmp_path / name
    fragment = root / DEFAULT_FRAGMENT
    fragment.parent.mkdir(parents=True)
    names = ", ".join(f'"{dep}"' for dep in depends_on)
    fragment.write_text(f"[module]\ndepends_on = [{names}]\n", encoding="utf-8")
    return root


def _sibling(tmp_path):
    """Return a locator that finds a module as a directory under *tmp_path*."""
    def locate(name):
        """Return the sibling directory when it exists."""
        path = tmp_path / name
        return path if path.is_dir() else None
    return locate


def test_a_module_with_no_dependencies_is_its_own_closure(tmp_path):
    """Check that a module with no dependencies is its own closure."""
    root = _module(tmp_path, "sushiruntime")
    closure = resolve("sushiruntime", root, _sibling(tmp_path))
    assert closure.sources == ((root / DEFAULT_FRAGMENT, "sushiruntime"),)
    assert closure.missing == ()


def test_a_chain_is_ordered_dependencies_first(tmp_path):
    """Check that a chain is ordered dependencies first."""
    _module(tmp_path, "sushiruntime")
    _module(tmp_path, "sushiblas", ["sushiruntime"])
    root = _module(tmp_path, "sushiai", ["sushiruntime", "sushiblas"])
    closure = resolve("sushiai", root, _sibling(tmp_path))
    assert [owner for _path, owner in closure.sources] == [
        "sushiruntime", "sushiblas", "sushiai"]


def test_shared_fragments_come_first(tmp_path):
    """Check that shared fragments come first."""
    root = _module(tmp_path, "sushiruntime")
    base = tmp_path / "base.deps.toml"
    base.write_text("", encoding="utf-8")
    closure = resolve("sushiruntime", root, _sibling(tmp_path), shared=[(base, "shared")])
    assert closure.sources[0] == (base, "shared")


def test_a_missing_checkout_is_reported_with_who_wanted_it(tmp_path):
    """Check that a missing checkout is reported with who wanted it."""
    root = _module(tmp_path, "sushiblas", ["sushiruntime"])
    closure = resolve("sushiblas", root, _sibling(tmp_path))
    assert closure.missing == (("sushiruntime", "sushiblas"),)
    assert [owner for _path, owner in closure.sources] == ["sushiblas"]


def test_a_missing_middle_module_hides_nothing_above_it(tmp_path):
    """Check that a missing middle module hides nothing above it."""
    _module(tmp_path, "sushiruntime")
    root = _module(tmp_path, "sushiai", ["sushiruntime", "sushiblas"])
    closure = resolve("sushiai", root, _sibling(tmp_path))
    assert closure.missing == (("sushiblas", "sushiai"),)
    assert [owner for _path, owner in closure.sources] == ["sushiruntime", "sushiai"]


def test_a_checkout_without_a_fragment_is_present_and_empty(tmp_path):
    """Check that a checkout without a fragment is present and empty."""
    (tmp_path / "sushiruntime").mkdir()
    root = _module(tmp_path, "sushiblas", ["sushiruntime"])
    closure = resolve("sushiblas", root, _sibling(tmp_path))
    assert closure.missing == ()
    assert [owner for _path, owner in closure.sources] == ["sushiblas"]


def test_a_cycle_raises(tmp_path):
    """Check that a cycle raises."""
    _module(tmp_path, "a", ["b"])
    root = _module(tmp_path, "b", ["a"])
    with pytest.raises(ValueError, match="cycle"):
        resolve("b", root, _sibling(tmp_path))


def test_a_module_without_its_own_fragment_resolves_to_shared_only(tmp_path):
    """Check that a module without its own fragment resolves to shared only."""
    root = tmp_path / "bare"
    root.mkdir()
    assert resolve("bare", root, _sibling(tmp_path)).sources == ()
```

- [ ] **Step 2: Run** `python -m pytest tests/provision/test_closure.py -q`. Expected: FAIL, no module.

- [ ] **Step 3: Implement:**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Collects the fragments one module needs: its own and every module's it builds on."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

from sushicore import deps_fragment

#: Path of a module's fragment, relative to its checkout.
DEFAULT_FRAGMENT = "cli/sushistack.deps.toml"

#: Finds the checkout of the module a fragment names, or None when there is none.
Locate = Callable[[str], Optional[Path]]


@dataclass(frozen=True)
class Closure:
    """The fragments to read, dependencies first, and the modules with no checkout."""

    sources: tuple[tuple[Path, str], ...]
    missing: tuple[tuple[str, str], ...]


def resolve(key: str, root: Path, locate: Locate, *, fragment: str = DEFAULT_FRAGMENT,
            shared: Sequence[tuple[Path, str]] = ()) -> Closure:
    """Return the closure of the module *key* checked out at *root*.

    Args:
        key: The module's lower-cased name.
        root: The module's checkout.
        locate: Finds the checkout of a module named in ``depends_on``.
        fragment: The module's own fragment, relative to *root*.
        shared: Fragments placed before every module's.

    Raises:
        ValueError: The modules depend on one another in a cycle.
    """
    sources: list[tuple[Path, str]] = list(shared)
    missing: list[tuple[str, str]] = []
    done: set[str] = set()

    def visit(name: str, checkout: Path, relative: str, trail: tuple[str, ...]) -> None:
        """Append *name*'s dependencies, then *name*, to the closure."""
        if name in trail:
            raise ValueError(
                "Modules depend on one another in a cycle: " + " -> ".join((*trail, name)))
        if name in done:
            return
        done.add(name)
        path = checkout / relative
        if not path.is_file():
            return
        for dependency in deps_fragment.read(path).depends_on:
            found = locate(dependency)
            if found is None:
                if (dependency, name) not in missing:
                    missing.append((dependency, name))
                continue
            visit(dependency, found, DEFAULT_FRAGMENT, (*trail, name))
        sources.append((path, name))

    visit(key, root, fragment, ())
    return Closure(tuple(sources), tuple(missing))
```

The cycle test needs the trail check to run before the `done` check, as written.

- [ ] **Step 4: Run** the sushicore suite. Changelog: `- 2026-10-04 — provision: Added the dependency closure that follows a fragment's depends_on to each module's checkout (`sushicore/provision/closure.py`).`

Acceptance: suite green.

---

### Task 6: Two stock doctor checks

**Files:**
- Modify: `D:/Projects/sushicore/sushicore/provision/checks.py`
- Test: `D:/Projects/sushicore/tests/provision/test_checks.py`

**Interfaces:**
- Consumes: `Closure.missing`, `selection.toolchain_keys`, `probe.toolchain_status`.
- Produces:
  - `modules_check(missing: Sequence[tuple[str, str]], fix: str) -> FunctionCheck`, name `"modules"`, group `"build"`, required. OK with detail `"every module this one builds on is checked out"`; FAIL with detail `"no checkout of: sushiruntime (wanted by sushiblas)"`, comma-joined.
  - `capability_check(source: IDependencySource, present: Mapping[str, bool], fix: str) -> FunctionCheck`, name `"toolchains"`, group `"build"`, required. One FAIL detail per capability with no present member: `"sycl-toolchain: none of intel-llvm, adaptivecpp, oneapi"`. OK detail lists the present member of each group, or `"no toolchain declared"`.

`checks` and `selection` are both layer 2 and `capability_check` calls `selection.groups(source)`; the layering guard allows a sideways import, so no layer moves.

- [ ] **Step 1: Failing tests** appended to `tests/provision/test_checks.py`, reusing `_Source` and `_sycl` copied from `test_selection.py` into this file:

```python
def test_modules_check_passes_with_nothing_missing():
    """Check that modules check passes with nothing missing."""
    assert checks.modules_check((), "sb setup").run().state is State.OK


def test_modules_check_fails_and_names_each_missing_module():
    """Check that modules check fails and names each missing module."""
    result = checks.modules_check((("sushiruntime", "sushiblas"),), "clone it").run()
    assert result.state is State.FAIL
    assert "sushiruntime (wanted by sushiblas)" in result.detail
    assert result.fix == "clone it"


def test_capability_check_fails_for_an_unsatisfied_group():
    """Check that capability check fails for an unsatisfied group."""
    source = _Source([_sycl("intel-llvm"), _sycl("adaptivecpp")])
    result = checks.capability_check(source, {}, "sr setup").run()
    assert result.state is State.FAIL
    assert "sycl-toolchain: none of intel-llvm, adaptivecpp" in result.detail


def test_capability_check_passes_when_one_member_is_present():
    """Check that capability check passes when one member is present."""
    source = _Source([_sycl("intel-llvm"), _sycl("adaptivecpp")])
    result = checks.capability_check(source, {"adaptivecpp": True}, "sr setup").run()
    assert result.state is State.OK
    assert "adaptivecpp" in result.detail


def test_capability_check_passes_when_nothing_is_declared():
    """Check that capability check passes when nothing is declared."""
    result = checks.capability_check(_Source([]), {}, "sd setup").run()
    assert (result.state, result.detail) == (State.OK, "no toolchain declared")
```

- [ ] **Step 2: Run** `python -m pytest tests/provision/test_checks.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** both as `FunctionCheck` factories beside `fragment_check`, in its style.
- [ ] **Step 4: Run** the sushicore suite. Changelog: `- 2026-10-04 — provision: Added doctor checks for missing module checkouts and unsatisfied toolchain capabilities (`sushicore/provision/checks.py`).`

Acceptance: suite green, `test_layering.py` included.

---

### Task 7: The commands carry the closure and the selection

**Files:**
- Modify: `D:/Projects/sushicore/sushicore/provision/commands.py`
- Test: `D:/Projects/sushicore/tests/provision/test_commands.py`

**Interfaces:**
- Consumes: Tasks 1 to 6.
- Produces, on `ModuleProvision`:
  - `locate: Locate = lambda name: None`
  - `panel: str | None = None`
  - `is_binary: Callable[[], bool] = lambda: False`
  - `uses_base: bool = False`
- `setup` options: `--dry-run`, `--yes`, `--toolchain NAME` (repeatable), `--no-gpu`.
- Exit codes: 2 for an unknown `--toolchain` and for a missing `depends_on` checkout; 1 for a lock timeout or a failed step; otherwise doctor's.

Behaviour:
- `_closure(module, root)` calls `closure.resolve(module.profile.key, root, module.locate, fragment=module.fragment, shared=[(manifests.base_fragment(), manifests.BASE_OWNER)] if module.uses_base else ())`. A `ValueError` from a cycle is printed with `console.error` and exits 1.
- `setup`: resolve the closure; when `missing` is not empty, print one `console.error` per pair, `"{wanted_by} builds on {module}, and no checkout of it was found. Clone it beside this repository or set {MODULE}_DIR."` with `{MODULE}` upper-cased, and exit 2 before the lock. Then derive the selection from `{name: present for name, present, _ in probe.toolchain_status(cfg, False)}` with `requested` and `gpu=not no_gpu`; a `ValueError` is printed and exits 2. Then the pipeline as today, with `selection=` and `active_toolchain=None`.
- `doctor`: same closure. `missing` does not stop it; it becomes `modules_check`. Checks are `standard_checks + [modules_check, capability_check, fragment_check, stamp_check] + extra_checks`. `fragment_check`'s `gpu` argument stays `False`.
- When `module.is_binary()` is true, only `doctor` is registered, its checks are `[python_check()] + module.extra_checks()`, and its fix text is `"hub install"`.
- Every registered command gets `rich_help_panel=module.panel` when it is not `None`.
- `_warn_unread_depends_on` and its test are deleted.

- [ ] **Step 1: Failing tests** appended to `tests/provision/test_commands.py`. `_app` gains keyword arguments it forwards to `ModuleProvision` (`**overrides`); existing callers are unchanged.

```python
def _sibling_locator(tmp_path):
    """Return a locator finding modules as directories under *tmp_path*."""
    def locate(name):
        """Return the sibling directory when it exists."""
        path = tmp_path / name
        return path if path.is_dir() else None
    return locate


def _depending_fragment(root, depends_on):
    """Write a fragment under *root* that depends on *depends_on* and declares a widget."""
    fragment = _write_fragment(root)
    names = ", ".join(f'"{name}"' for name in depends_on)
    fragment.write_text(f"[module]\ndepends_on = [{names}]\n"
                        + fragment.read_text(encoding="utf-8"), encoding="utf-8")


def test_setup_exits_two_and_installs_nothing_when_a_module_is_missing(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that setup exits two and installs nothing when a module is missing."""
    installs = []

    class _Recording(_FakeAptManager):
        """Records every install call."""

        def install(self, pkgs, dry_run):
            """Record the call and report success."""
            installs.append(pkgs)
            return True

    _quiet_setup(monkeypatch, provision_home, managers=[_Recording()])
    _depending_fragment(tmp_path / "dsp", ["sushiruntime"])
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path))

    result = CliRunner().invoke(app, ["setup"])

    assert result.exit_code == 2
    errors = [args[0] for name, args in recording_console.calls if name == "error"]
    assert any("sushiruntime" in e and "SUSHIRUNTIME_DIR" in e for e in errors)
    assert installs == []
    assert not (provision_home / ".lock").exists()
    assert not (tmp_path / "dsp" / "cli" / "config.local.toml").exists()


def test_setup_reads_the_fragment_of_a_located_dependency(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that setup reads the fragment of a located dependency."""
    _quiet_setup(monkeypatch, provision_home, managers=[])
    runtime = tmp_path / "sushiruntime" / "cli" / "sushistack.deps.toml"
    runtime.parent.mkdir(parents=True)
    runtime.write_text('[gadget]\ndescription = "g"\nlinux_apt = ["gadget-dev"]\n',
                       encoding="utf-8")
    _depending_fragment(tmp_path / "dsp", ["sushiruntime"])
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path))

    result = CliRunner().invoke(app, ["setup", "--dry-run"])

    assert result.exit_code == 0, result.exception
    rows = _table_rows(recording_console.calls, ["Component", "Status", "Owner", "Detail"])
    owners = {row[0]: row[2] for row in rows}
    assert owners["gadget"] == "sushiruntime"
    assert owners["widget"] == "sushidsp"


def test_setup_rejects_an_unknown_toolchain_before_the_lock(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that setup rejects an unknown toolchain before the lock."""
    _quiet_setup(monkeypatch, provision_home, managers=[])
    _write_fragment(tmp_path / "dsp")
    result = CliRunner().invoke(_app(tmp_path, recording_console),
                                ["setup", "--dry-run", "--toolchain", "typo"])
    assert result.exit_code == 2
    assert not (provision_home / ".lock").exists()


def test_setup_selects_the_first_declared_toolchain_when_none_is_present(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that setup selects the first declared toolchain when none is present."""
    _quiet_setup(monkeypatch, provision_home, managers=[])
    seen = []
    monkeypatch.setattr(commands.InstallPipeline, "run",
                        lambda self, ctx, show_progress=True: seen.append(ctx.selection) or True)
    monkeypatch.setattr(probe, "toolchain_status", lambda cfg, gpu: [
        ("intel-llvm", False, ""), ("adaptivecpp", False, ""), ("oneapi", False, "")])
    fragment = _write_fragment(tmp_path / "dsp")
    fragment.write_text(
        '[intel-llvm]\nprovides = "sycl-toolchain"\n[adaptivecpp]\nprovides = "sycl-toolchain"\n',
        encoding="utf-8")

    CliRunner().invoke(_app(tmp_path, recording_console), ["setup", "--dry-run", "--no-gpu"])

    assert (seen[0].install_intel_llvm, seen[0].install_acpp, seen[0].gpu) == (
        True, False, False)


def test_setup_selects_nothing_when_a_toolchain_is_present(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that setup selects nothing when a toolchain is present."""
    _quiet_setup(monkeypatch, provision_home, managers=[])
    seen = []
    monkeypatch.setattr(commands.InstallPipeline, "run",
                        lambda self, ctx, show_progress=True: seen.append(ctx.selection) or True)
    monkeypatch.setattr(probe, "toolchain_status", lambda cfg, gpu: [
        ("intel-llvm", True, ""), ("adaptivecpp", False, ""), ("oneapi", False, "")])
    fragment = _write_fragment(tmp_path / "dsp")
    fragment.write_text(
        '[intel-llvm]\nprovides = "sycl-toolchain"\n[adaptivecpp]\nprovides = "sycl-toolchain"\n',
        encoding="utf-8")

    CliRunner().invoke(_app(tmp_path, recording_console), ["setup", "--dry-run"])

    assert not (seen[0].install_intel_llvm or seen[0].install_acpp)


def test_uses_base_adds_the_shared_fragment(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that uses base adds the shared fragment."""
    _quiet_setup(monkeypatch, provision_home, managers=[])
    _write_fragment(tmp_path / "dsp")
    app = _app(tmp_path, recording_console, uses_base=True)

    CliRunner().invoke(app, ["setup", "--dry-run"])

    rows = _table_rows(recording_console.calls, ["Component", "Status", "Owner", "Detail"])
    assert any(row[0] == "gtest" and row[2] == "shared" for row in rows)


def test_doctor_reports_a_missing_module_and_keeps_running(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that doctor reports a missing module and keeps running."""
    monkeypatch.setattr(commands, "standard_checks", lambda cfg, fix: [])
    _depending_fragment(tmp_path / "dsp", ["sushiruntime"])
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path))

    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 1
    rows = _table_rows(recording_console.calls, ["Check", "Group", "Result", "Detail", "Fix"])
    by_name = {row[0]: row for row in rows}
    assert "sushiruntime" in by_name["modules"][3]
    assert "dependencies" in by_name


def test_a_binary_install_registers_doctor_alone(tmp_path, recording_console):
    """Check that a binary install registers doctor alone."""
    app = _app(tmp_path, recording_console, is_binary=lambda: True)
    names = {command.callback.__name__ for command in app.registered_commands}
    assert names == {"doctor"}


def test_the_panel_is_set_on_every_command(tmp_path, recording_console):
    """Check that the panel is set on every command."""
    app = _app(tmp_path, recording_console, panel="Environment")
    assert {command.rich_help_panel for command in app.registered_commands} == {"Environment"}
```

Delete `test_setup_warns_for_each_depends_on_module_it_cannot_read`.

- [ ] **Step 2: Run** `python -m pytest tests/provision/test_commands.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** to the behaviour above. Keep `register_provision_commands` readable by lifting `setup`'s body into `_run_setup(module, *, dry_run, yes, toolchains, gpu) -> int` and the check list into `_checks(module, cfg, closure_result, fix) -> list[Check]`.
- [ ] **Step 4: Run** the sushicore suite, then sd's and st's (`cd D:/Projects/sushidsp/cli && python -m pytest -q`; `cd D:/Projects/sushitrack/cli && python -m pytest -q`), then `sd doctor`, `sd setup --dry-run`, `st doctor`. Paste all. Changelog: `- 2026-10-04 — provision: Made setup follow depends_on, choose toolchains by the selection rule and take --toolchain and --no-gpu (`sushicore/provision/commands.py`).`

Acceptance: three suites green; `sd setup --dry-run` exits as before; `sd doctor` gains the `modules` and `toolchains` rows.

---

### Task 8: `StackConfig` resolves through the dependency roots

**Files:**
- Modify: `D:/Projects/sushicore/sushicore/stack_config.py`
- Modify: `D:/Projects/sushicore/sushicore/build_env.py:198`
- Test: `D:/Projects/sushicore/tests/test_stack_config.py` (new)

**Interfaces:**
- Produces on `StackConfig`:
  - It derives from `ProvisionSettings`, so it carries `oneapi_root`, `icx_compiler`, `llvm_root`, `acpp_exe`.
  - `dependency_roots(root: Path) -> list[Path]`: `[SUSHISTACK_DEPS_DIR]` when set; else `<workspace>/dependencies` when `workspace_home(root)` finds one, followed by `provision.home.search_roots()`, duplicates removed, order kept.
  - `deps_dir(root)` returns `dependency_roots(root)[0]`. Its signature does not change.
  - `locate_sibling(root: Path, name: str) -> Path | None`: `sibling_dir(root, name, getattr(self, f"{name}_dir", ""))` when it is a directory, else `None`.
  - `standalone_deps_dir` stays as a method returning `provision.home.root()` and is marked deprecated in its docstring; Tasks 11 to 13 and 16 delete the overrides, and the method itself goes in a later release (`api-stability`).
- `bundled_clang` returns `llvm_root`'s clang++ when `llvm_root` is set and the file exists, else the first `<root>/toolchains/llvm-sycl/bin/clang++` across `dependency_roots`. `resolved_vcpkg` returns the first `<root>/vcpkg` directory. `build_env.py:198` uses the same search through a new `StackConfig.bundled_llvm_root(root) -> Path | None`, which `bundled_clang` also calls.

- [ ] **Step 1: Failing tests:**

```python
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the toolchain resolution of a module that consumes the shared tree."""

from __future__ import annotations

from dataclasses import dataclass

from sushicore.provision.config import ProvisionSettings
from sushicore.stack_config import StackConfig


@dataclass
class _Config(StackConfig):
    """A stack config naming one sibling."""

    sushiruntime_dir: str = ""


def _clang(root):
    """Create a clang++ under *root*'s llvm-sycl bundle and return it."""
    exe = root / "toolchains" / "llvm-sycl" / "bin" / "clang++"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    return exe


def test_a_stack_config_carries_the_provision_fields():
    """Check that a stack config carries the provision fields."""
    assert issubclass(StackConfig, ProvisionSettings)


def test_bundled_clang_is_found_under_the_provision_root(provision_home, tmp_path):
    """Check that bundled clang is found under the provision root."""
    exe = _clang(provision_home)
    assert _Config(platform="linux").bundled_clang(tmp_path) == str(exe)


def test_a_workspace_tree_wins_over_the_provision_root(provision_home, tmp_path):
    """Check that a workspace tree wins over the provision root."""
    workspace = tmp_path / "ws"
    (workspace / ".sushistack").mkdir(parents=True)
    module = workspace / "sushiblas"
    module.mkdir()
    _clang(provision_home)
    exe = _clang(workspace / "dependencies")
    assert _Config(platform="linux").bundled_clang(module) == str(exe)


def test_the_environment_override_is_the_only_root(provision_home, tmp_path, monkeypatch):
    """Check that the environment override is the only root."""
    _clang(provision_home)
    monkeypatch.setenv("SUSHISTACK_DEPS_DIR", str(tmp_path / "empty"))
    assert _Config(platform="linux").bundled_clang(tmp_path) == ""


def test_resolved_vcpkg_finds_the_provision_root_tree(provision_home, tmp_path):
    """Check that resolved vcpkg finds the provision root tree."""
    (provision_home / "vcpkg").mkdir(parents=True)
    assert _Config(platform="linux").resolved_vcpkg(tmp_path) == str(provision_home / "vcpkg")


def test_locate_sibling_returns_the_directory_beside_the_root(tmp_path):
    """Check that locate sibling returns the directory beside the root."""
    root = tmp_path / "sushiblas"
    root.mkdir()
    (tmp_path / "sushiruntime").mkdir()
    found = _Config(platform="linux").locate_sibling(root, "sushiruntime")
    assert found == (tmp_path / "sushiruntime").resolve()


def test_locate_sibling_prefers_the_configured_directory(tmp_path):
    """Check that locate sibling prefers the configured directory."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    cfg = _Config(platform="linux", sushiruntime_dir=str(elsewhere))
    assert cfg.locate_sibling(tmp_path / "sushiblas", "sushiruntime") == elsewhere.resolve()


def test_locate_sibling_is_none_without_a_checkout(tmp_path):
    """Check that locate sibling is none without a checkout."""
    assert _Config(platform="linux").locate_sibling(tmp_path / "x", "sushiruntime") is None
```

Move the `provision_home` fixture from `tests/provision/conftest.py` to `tests/conftest.py` so both directories see it; leave `recording_console` where it is.

- [ ] **Step 2: Run** `python -m pytest tests/test_stack_config.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement.** `stack_config` imports `provision.home` and `provision.config`; both are layer 0 of `provision` and import only `workspace` and `config_base`, so no cycle forms. Confirm with `python -c "import sushicore.stack_config"`.
- [ ] **Step 4: Run** the sushicore suite and the suites of every consumer: hub, sb, sa, se (`cd D:/Projects/<repo>/cli && python -m pytest -q`). For se run `python -m pytest -q tests/test_config_contracts.py tests/test_doctor.py tests/test_status.py tests/test_configure_arguments.py` if the full suite needs the `planet` extra. Then `sb config`, `sa config`, `se config`: the compiler and vcpkg lines must read as before. Paste all. Changelog: `- 2026-10-04 — config: Made StackConfig resolve the compiler and vcpkg across every dependency root and locate sibling checkouts (`sushicore/stack_config.py`, `sushicore/build_env.py`).`

Acceptance: every suite green and the three `config` outputs unchanged.

---

### Task 9: sushicore 0.7.0

**Files:**
- Modify: `D:/Projects/sushicore/pyproject.toml` (version `0.7.0`)
- Modify: `D:/Projects/sushicore/README.md` (Provisioning section)
- Modify: `D:/Projects/sushicore/docs/reference/CHANGELOG.md`
- Modify: `D:/Projects/sushicore/docs/agent/specs/2026-10-04-standalone-provision-design.md` (status line)

- [ ] **Step 1:** README's Provisioning section gains: what `setup` installs by default and how `--toolchain` and `--no-gpu` change it; that `depends_on` is followed to sibling checkouts and what happens when one is missing; the four `ModuleProvision` fields; the search order of the dependency roots. Run the `humanizer` pass.
- [ ] **Step 2:** Bump the version. Do not tag.
- [ ] **Step 3: Run** the sushicore suite, hub's, sd's and st's; paste the four tails.
- [ ] **Step 4:** Commit by path: `chore(release): prepare sushicore 0.7.0`.

Acceptance: four suites green on the 0.7.0 working tree.

---

## Wave 2: the module contract

Every wave-2 task follows this section. The dispatch prompt carries it whole, after the six delegation lines of the owner's `CLAUDE.md`.

**What a module CLI does:**

1. Its `Config` carries the provision fields. A `StackConfig` subclass already does after Task 8.
2. `cli.py` registers the shared commands once, after its own commands:

```python
from sushicore.provision.commands import ModuleProvision, register_provision_commands

register_provision_commands(app, ModuleProvision(
    profile=PROFILE,
    project_root=find_project_root,
    load_config=load_config,
    console=lambda: console,
    locate=lambda name: load_config().locate_sibling(find_project_root(), name),
    panel=<the panel constant the task names>,
    uses_base=True,
))
```

3. Any `standalone_deps_dir` override, any private `deps_dir`, and any loop that re-panels the provision commands is deleted.
4. `cli/pyproject.toml` requires `sushicore>=0.7.0`.
5. `cli/tests/test_provision_commands.py` exists, in this shape, with the module's names:

```python
"""Tests that <prog> carries the shared provision commands."""

from __future__ import annotations

from typer.testing import CliRunner

from sushicore.provision.config import ProvisionSettings
from <package>.cli import app
from <package>.config import Config


def test_the_four_provision_commands_are_registered():
    """Assert setup, doctor, link and unlink appear in the help."""
    out = CliRunner().invoke(app, ["--help"]).output
    for name in ("setup", "doctor", "link", "unlink"):
        assert name in out


def test_setup_takes_the_shared_options():
    """Assert setup offers --dry-run, --toolchain and --no-gpu."""
    out = CliRunner().invoke(app, ["setup", "--help"]).output
    for option in ("--dry-run", "--toolchain", "--no-gpu"):
        assert option in out


def test_config_is_a_provision_config():
    """Assert the config carries every field provision reads."""
    assert issubclass(Config, ProvisionSettings)
```

   and the module's `tests/test_help_screen.py` lists the four commands under the panel.
6. The module's CLI documentation gains a section for the four commands, found with `grep -rn "<prog> doctor\|<prog> config\|hub install" README.md docs --include=*.md`. Every sentence that tells a reader to run `hub install` before building is rewritten to name `<prog> setup`, with hub named as the way to provision several checkouts at once. Run the `humanizer` pass.
7. The changelog line is handed to the controller in the report, not written, when the changelog file is dirty in `git status --short`; otherwise it is written under `## Unreleased`.

**What the report must paste:** the output of the module's pytest run; `<prog> --help`; `<prog> setup --dry-run`; `<prog> doctor`; `git status --short -- cli`; a syntax check of every file written (`python -m py_compile <file>`); the scratchpad size.

**What the reviewer checks, as named items:** SOLID shape (one registration call, no setup logic in the module, nothing duplicated from sushicore); humanizer register of the documentation and docstrings; that `setup --dry-run` wrote nothing (`git status --short`); that no build ran.

---

### Task 10: `sr`

**Files** (repository `D:/Projects/sushiruntime`):
- Modify: `cli/sushiruntime/config.py`, `cli/sushiruntime/cli.py`, `cli/sushiruntime/services/select.py:28`, `cli/pyproject.toml`
- Create: `cli/tests/test_provision_commands.py`
- Modify: `cli/tests/test_help_screen.py`, the CLI documentation, `docs/reference/CHANGELOG.md`

**Interfaces:**
- Consumes: the contract; `probe.installed_toolchain(name, relative)`; `ProvisionSettings`.

Specific to `sr`:
- `class Config(ProvisionSettings)`; the four field declarations it shares with `ProvisionSettings` (`oneapi_root`, `icx_compiler`, `llvm_root`, `acpp_exe`) are removed, their comments kept above the class docstring's field list.
- `deps_dir()` and `sushistack_home()` are deleted. `resolved_llvm_root` returns the pinned `llvm_root`, else `str(found.parents[1])` for the first `probe.installed_toolchain(name, Path("bin") / compiler)` over `INTEL_LLVM_BUNDLE_DIRS`. `services/select.py:28` lists toolchains under every `home.search_roots()` entry's `toolchains/`.
- `locate` is omitted: `sr` depends on no module.
- `panel=K_DIAGNOSTICS`.
- `sr` no longer falls back to `<repo>/dependencies`. The changelog line says so: `- 2026-10-04 — cli: Added setup, doctor, link and unlink from sushicore and stopped reading a repo-local dependencies folder (`cli/sushiruntime/cli.py`, `cli/sushiruntime/config.py`).`

Extra tests in `cli/tests/test_config.py`:

```python
def test_llvm_root_is_found_under_the_provision_root(tmp_path, monkeypatch):
    """Assert a bundle under ~/.sushisystems is the resolved llvm root."""
    monkeypatch.setenv("SUSHISYSTEMS_HOME", str(tmp_path))
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    monkeypatch.delenv("SUSHISTACK_DEPS_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    cfg = Config(platform="linux")
    exe = tmp_path / "toolchains" / "llvm-sycl" / "bin" / "clang++"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    assert cfg.resolved_llvm_root() == str(tmp_path / "toolchains" / "llvm-sycl")


def test_a_pinned_llvm_root_wins(tmp_path, monkeypatch):
    """Assert an explicit llvm_root is returned without probing."""
    monkeypatch.setenv("SUSHISYSTEMS_HOME", str(tmp_path))
    assert Config(platform="linux", llvm_root="/opt/llvm").resolved_llvm_root() == "/opt/llvm"
```

Acceptance: `sr` suite green; `sr setup --dry-run` lists `shared` and `sushiruntime` owners and, on this machine, selects no toolchain download; `sr config` reads as before.

---

### Task 11: `sb`

**Files** (repository `D:/Projects/sushiblas`):
- Modify: `cli/sushiblas/config.py` (delete `standalone_deps_dir`; the module docstring's sentence about borrowing the runtime's bundle goes with it), `cli/sushiblas/cli.py`, `cli/pyproject.toml`
- Create: `cli/tests/test_provision_commands.py`
- Modify: `cli/tests/test_help_screen.py`, the CLI documentation, the changelog

Specific to `sb`: `panel=K_DIAGNOSTICS`. One extra test:

```python
def test_setup_stops_when_the_runtime_checkout_is_missing(tmp_path, monkeypatch):
    """Assert setup exits 2 and names sushiruntime when it has no checkout."""
    root = tmp_path / "sushiblas"
    (root / "cli").mkdir(parents=True)
    (root / "CMakeLists.txt").write_text("")
    (root / "cli" / "config.toml").write_text("")
    (root / "cli" / "sushistack.deps.toml").write_text(
        '[module]\ndepends_on = ["sushiruntime"]\n')
    monkeypatch.chdir(root)
    monkeypatch.setenv("SUSHISYSTEMS_HOME", str(tmp_path / "home"))
    for name in ("SUSHISTACK_HOME", "SUSHIRUNTIME_DIR", "SUSHISTACK_DEPS_DIR"):
        monkeypatch.delenv(name, raising=False)
    result = CliRunner().invoke(app, ["setup", "--dry-run"])
    assert result.exit_code == 2
    assert "sushiruntime" in result.output
```

Changelog: `- 2026-10-04 — cli: Added setup, doctor, link and unlink from sushicore (`cli/sushiblas/cli.py`, `cli/sushiblas/config.py`).`

Acceptance: `sb` suite green; `sb setup --dry-run` lists owners `shared`, `sushiruntime`, `sushiblas` in that order.

---

### Task 12: `sa`

**Files** (repository `D:/Projects/sushiai`): as Task 11, under `cli/sushiai/`.

Specific to `sa`: `panel=K_DIAGNOSTICS`; if `cli.py` names its panels differently, use the one `config` and `env` sit under. The extra test is Task 11's with `sushiai`, `depends_on = ["sushiruntime", "sushiblas"]`, `SUSHIBLAS_DIR` added to the cleared variables, and both names asserted in the output.

Changelog: `- 2026-10-04 — cli: Added setup, doctor, link and unlink from sushicore (`cli/sushiai/cli.py`, `cli/sushiai/config.py`).`

Acceptance: `sa` suite green; `sa setup --dry-run` lists owners `shared`, `sushiruntime`, `sushiblas`, `sushiai` in that order.

---

### Task 13: `se`

**Files** (repository `D:/Projects/sushiengine`, `cli/` only):
- Modify: `cli/sushiengine/config.py` (delete `standalone_deps_dir`), `cli/sushiengine/cli.py` (delete the `doctor` command and the `doctor_svc` import; register the shared commands), `cli/sushiengine/services/doctor.py`, `cli/pyproject.toml`
- Modify: `cli/tests/test_doctor.py`, `cli/tests/test_help_screen.py`, `cli/tests/test_command_tree.py`, `cli/tests/test_cli_commands.py` (the lists naming top-level commands gain `setup`, `link`, `unlink`)
- Create: `cli/tests/test_provision_commands.py`
- Modify: `cli/README.md`, `docs/reference/CHANGELOG.md` (report the line if the file is dirty)

**Interfaces:**
- Produces in `services/doctor.py`:
  - `engine_checks() -> list[Check]` for a source checkout: `root marker`, `extra planet`, `extra climatology`, `extra dev`, `validation layer`, `docker`, `alias dates`, each a `sushicore.provision.doctor.FunctionCheck` in group `build`, with `required=True` for `root marker` and `False` for the rest. The detail text of each is today's.
  - `release_checks() -> list[Check]` for a binary install: `release manifest` (the file `PROFILE.release_manifest` exists at the root, required) and `licence` (the file `sushi-licence.jwt` exists beside it, required), each with fix `hub add sushiengine`.
  - `is_binary() -> bool`: `_MODULE.presence() == "binary"`, and `False` when `find_project_root` raises `SystemExit`.
- The checks `runtime sibling`, `compiler`, `vcpkg`, `cmake`, `ninja`, `ctest` and `doxygen`, the local `Check` dataclass, `diagnose` and `show` are deleted; sushicore's `modules`, `c++ compiler`, `cmake`, `ctest` and `ninja` rows replace them. `doxygen` moves to `engine_checks` as `tool_check("doxygen", cfg.doxygen_exe or "doxygen", required=False)`.
- Registration: the contract's call with `panel=K_ENVIRONMENT`, `extra_checks=lambda: doctor_svc.release_checks() if doctor_svc.is_binary() else doctor_svc.engine_checks()`, `is_binary=doctor_svc.is_binary`.

`cli/tests/test_doctor.py` is rewritten against the two functions: each engine check's pass and fail detail, `release_checks` with and without each file, `is_binary` in a directory carrying `sushi-release.json`, in one carrying `.sushiengine-root`, and outside both.

Extra tests in `cli/tests/test_provision_commands.py`:

```python
def test_a_source_checkout_carries_all_four(monkeypatch, tmp_path):
    """Assert the help outside any project lists the four commands and raises nothing."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in ("setup", "doctor", "link", "unlink"):
        assert name in result.output
```

`se` does not publish a binary command set yet, so the binary branch is covered by `is_binary` and `release_checks` unit tests and by sushicore's `test_a_binary_install_registers_doctor_alone`.

The subagent reads `git -C D:/Projects/sushiengine status --short -- cli` first and lists any file under `cli/` that is already dirty; it edits such a file only in the hunks this task names and says so in the report.

Changelog: `- 2026-10-04 — cli: Added setup, link and unlink from sushicore and moved se doctor onto the shared doctor table (`cli/sushiengine/cli.py`, `cli/sushiengine/services/doctor.py`).`

Acceptance: the `se` suites the task touches are green (`tests/test_doctor.py`, `tests/test_provision_commands.py`, `tests/test_help_screen.py`, `tests/test_command_tree.py`, `tests/test_cli_commands.py`, `tests/test_config_contracts.py`); `se doctor` prints the shared table with the engine's rows; `se setup --dry-run` lists owners `shared`, `sushiruntime`, `sushiengine`.

---

### Task 14: `sd`

**Files** (repository `D:/Projects/sushidsp`): `cli/sushidsp/cli.py`, `cli/pyproject.toml`, `cli/tests/test_provision_commands.py`, `cli/tests/test_help_screen.py`.

Specific to `sd`: the registration gains `panel=K_ENVIRONMENT`; `K_PROVISION_COMMANDS` and the loop under it are deleted; `uses_base` and `locate` are omitted, because `sd` declares no `depends_on` and needs none of the SYCL base. `test_provision_commands.py` gains the contract's `--toolchain` and `--no-gpu` assertions. Documentation changes only where it names the options.

Changelog: `- 2026-10-04 — cli: Took the help panel of the provision commands from sushicore (`cli/sushidsp/cli.py`).`

Acceptance: `sd` suite green; `sd --help` lists the four commands under Environment as before.

---

### Task 15: `st`

**Files** (repository `D:/Projects/sushitrack`): `cli/sushitrack_cli/cli.py`, `cli/pyproject.toml`, `cli/tests/test_help_screen.py`.

Specific to `st`: read how `cli.py` places the four commands in its help today (`cli/tests/test_help_screen.py:94`); pass that panel as `panel=` and delete whatever re-panels them. `uses_base` and `locate` are omitted. The floor becomes `sushicore>=0.7.0`.

Changelog: `- 2026-10-04 — cli: Took the help panel of the provision commands from sushicore (`cli/sushitrack_cli/cli.py`).`

Acceptance: `st` suite green; `st --help` unchanged.

---

### Task 16: Hub reads the rule and the base fragment from sushicore

**Files** (repository `D:/Projects/sushistack`):
- Delete: `cli/sushihub/setup/selection.py`, `cli/sushihub/manifests/base.deps.toml`
- Modify: `cli/sushihub/setup/factory.py`, `cli/sushihub/setup/dependency_source.py`, `cli/sushihub/config.py` (delete `CUSTOMIZABLE_COMPONENTS`; `TOOLCHAINS` becomes `selection.toolchain_keys()`), `cli/sushihub/cli.py` (the `--customize` defaults), `cli/sushihub/services/customize.py`, `cli/sushihub/gui_config.py` (delete `standalone_deps_dir`), `cli/pyproject.toml` (`sushicore>=0.7.0`)
- Modify: every test importing `setup.selection` or `CUSTOMIZABLE_COMPONENTS` (`grep -rn "selection_from_source\|CUSTOMIZABLE_COMPONENTS\|MACHINE_COMPONENTS" cli`)
- Docs: `README.md`, `docs/getting_started/INSTALL.md`, `docs/design/WORKSPACE_DECOUPLING.md` (a dated paragraph in §2), `docs/design/REMAINING_WORK.md`, `docs/reference/CHANGELOG.md`, `cli/README.md`

**Interfaces:**
- Consumes: `selection.derive`, `selection.COMPONENTS`, `manifests.base_fragment`, `manifests.BASE_OWNER`.

- [ ] **Step 1: Failing tests.** In the test file that covers `build_pipeline`'s selection today:

```python
def test_a_bare_install_selects_one_sycl_toolchain(monkeypatch):
    """Assert the default selection is the first declared toolchain alone."""
    monkeypatch.setattr(probe, "toolchain_status", lambda cfg, gpu: [
        ("intel-llvm", False, ""), ("adaptivecpp", False, ""), ("oneapi", False, "")])
    _pipeline, ctx = build_pipeline(only="detect", cfg=_cfg(), source=_runtime_source(),
                                    managers=[])
    assert (ctx.selection.install_intel_llvm, ctx.selection.install_acpp,
            ctx.selection.oneapi) == (True, False, False)


def test_a_present_toolchain_selects_no_download(monkeypatch):
    """Assert an installed toolchain satisfies the group."""
    monkeypatch.setattr(probe, "toolchain_status", lambda cfg, gpu: [
        ("intel-llvm", True, ""), ("adaptivecpp", False, ""), ("oneapi", False, "")])
    _pipeline, ctx = build_pipeline(only="detect", cfg=_cfg(), source=_runtime_source(),
                                    managers=[])
    assert not ctx.selection.install_intel_llvm


def test_the_base_fragment_comes_from_sushicore():
    """Assert the shared fragment hub aggregates is sushicore's."""
    from sushicore.provision.manifests import base_fragment
    assert (base_fragment(), "shared") in manifest_sources()
```

`_cfg` and `_runtime_source` are that file's existing helpers for a config and a source declaring the three SYCL toolchains; read the file and use its names.

- [ ] **Step 2: Run** `cd D:/Projects/sushistack/cli && python -m pytest -q`. Expected: the three new tests FAIL.
- [ ] **Step 3: Implement.** `manifest_sources` starts with `(base_fragment(), BASE_OWNER)`, then hub's own shipped fragments, then the workspace's. `build_pipeline` computes `present` from `probe.toolchain_status(cfg, False)` and calls `selection.derive(source, present)`; a `--customize` result is merged over it with `ToolchainSelection.merged`, as today. `customize` reads labels from `selection.COMPONENTS`.
- [ ] **Step 4: Run** the hub suite, `hub install --dry-run`, `hub doctor`. Paste all. On this machine all three toolchains are present, so the dry run must select no toolchain download.
- [ ] **Step 5: Documentation.** `README.md` and `INSTALL.md` open the developer journey with the module's own `setup`, and present hub as what provisions several checkouts at once and what fetches the engine's binary. `WORKSPACE_DECOUPLING.md` §2 gains a paragraph dated 2026-10-04 recording the decision. `REMAINING_WORK.md`'s standalone section records what landed. Run the `humanizer` pass.

Changelog:
```
- 2026-10-04 — setup: Took the toolchain selection rule and the base fragment from sushicore, so a bare hub install installs one SYCL toolchain (`cli/sushihub/setup/factory.py`, `cli/sushihub/setup/dependency_source.py`).
```

- [ ] **Step 6: Commit** by path: `refactor(setup)!: take the selection rule and the base fragment from sushicore`.

Acceptance: hub suite green; `hub doctor` reports the same components as before the task.

---

### Task 17: Owner gate — real runs, then the release

The controller hands the owner each module's `setup --dry-run` and `doctor` output from wave 2 and hub's from wave 3.

The owner:
1. Runs the real `sr setup`, then `sr build`; then the same for `sb`, `sa`, `sd`, `st`, and `se` last.
2. Tags `v0.7.0` in sushicore and publishes it.
3. Pushes each repository.

Acceptance: every build passes. The dependency-root migration (`2026-09-25-hub-root-migration.md`) is next, with its sushicore bump renumbered to 0.8.0.

---

## Out of scope, recorded for the backlog

- Removing `StackConfig.standalone_deps_dir` itself, one release after its last override is gone.
- A binary command set for `se`; this plan only makes the registration ready for it.
- Reading a dependency module's `fragment` key from its `sushi-module.toml`. Every module uses the default path today.
- `st setup` creating the conda environment, still deferred in the SushiStack backlog.

## Deviations recorded while executing wave 1

- Task 2 also changed `VcpkgManager` and added `home.found_vcpkg_dir()`: without it an unlinked
  module on a machine holding a legacy tree would have bootstrapped a second vcpkg.
- Tasks 3 to 5 were written test and code together; their tests were never seen failing.
- Task 4: the GPU component turns on only when a declared dependency is `gpu_only`. Passing it
  through would have made `sd setup` install CUDA.
- Task 6: `selection.groups` returns a mapping from capability to members, so the check can name
  the capability. No layer moved.
- Task 8: `StackConfig.workspace_home` follows the module's `[link]` pointer, as
  `ModuleConfig.workspace_home` already did.
- `sushiai`'s `tests/test_demo.py` fails 9 tests on this machine before and after: it runs the
  installed `sa`, which holds sushicore 0.4.0, against a built demo whose SYCL kernel is not found.
- An optional toolchain (`required = false`, as `sd` declares intel/llvm) installs only under
  `--toolchain`, and the capability check ignores it. `selection.required_groups` holds the rule.
- `DetectStep` reports a declared toolchain as NOT NEEDED when another member of its capability
  is present, so `hub doctor` no longer lists AdaptiveCpp as missing beside a working intel/llvm.
- Tasks 14 and 15 were done by the controller, not by subagents: `sd` needed the `panel=` field
  and a corrected compiler hint, `st` needed its floor raised and nothing else.
- Task 16: hub keeps the GPU component on for every workspace by merging `{"gpu": True}` over
  sushicore's rule (`factory.derived_selection`), as `GPU_BACKEND_PROVISIONING.md` §3 decided.
  `selection.enabled_keys` and the shared-owner guard were added to sushicore for it.
- Tasks 10 to 13 are not started. The pipx environments of `sr`, `sb`, `sa` and `se` hold
  sushicore 0.4.0 from PyPI, so editing their `cli.py` before Task 0 would break the live commands.
