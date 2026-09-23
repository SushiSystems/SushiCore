# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The adapter builder fetches, configures, builds and stamps a Unified Runtime adapter."""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import tempfile
import typing
from pathlib import Path

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.gpu.adapter_builder import AdapterBuilder
from sushicore.provision.toolchains.stamp import TOOLCHAIN_STAMP, write_toolchain_stamp

_COMMIT = "d5f649b706f63b5c74e1929bc95db8de91085560"


@dataclasses.dataclass(frozen=True)
class _ToolkitInstall:
    """A located toolkit's install root and version, as the adapter builder reads it."""

    root: Path
    version: str | None


@dataclasses.dataclass(frozen=True)
class _GpuBackendSpec:
    """One vendor's build inputs, as the adapter builder reads them."""

    vendor: str
    adapter_option: str
    adapter_definitions: typing.Callable[[_ToolkitInstall], dict[str, str]]
    adapter_target: str
    adapter_binaries: tuple[str, ...]


class _FakeRunner:
    """Records every argv it was asked to run and fakes the adapter build output."""

    def __init__(self, build_dir: Path, binary_names: list[str],
                fail_on: str | None = None) -> None:
        """Store where the fake build output lands and which step should fail."""
        self._build_dir = build_dir
        self._binary_names = binary_names
        self._fail_on = fail_on
        self.calls: list[list[str]] = []

    def run(self, argv: list[str], cwd: Path | None,
           env: dict[str, str] | None) -> int:
        """Record *argv* and simulate the step it represents."""
        self.calls.append(argv)
        if self._fail_on and self._fail_on in argv:
            return 1
        if argv[:2] == ["cmake", "--build"]:
            output_dir = self._build_dir / "bin"
            output_dir.mkdir(parents=True, exist_ok=True)
            for name in self._binary_names:
                (output_dir / name).write_bytes(b"fake")
        return 0


class _MissingExecutableRunner:
    """Simulates git or cmake not being installed."""

    def run(self, argv: list[str], cwd: Path | None,
           env: dict[str, str] | None) -> int:
        """Raise as :func:`subprocess.Popen` would for an unknown executable."""
        raise FileNotFoundError(argv[0])


def _fake_spec(binary_bases: tuple[str, ...] = ("ur_adapter_fake",)) -> _GpuBackendSpec:
    """Return one backend spec whose fields exercise the adapter builder's plumbing."""
    return _GpuBackendSpec(
        vendor="fake",
        adapter_option="UR_BUILD_ADAPTER_FAKE",
        adapter_definitions=lambda install: {"FAKE_ROOT": str(install.root)},
        adapter_target="ur_adapter_fake",
        adapter_binaries=binary_bases,
    )


@pytest.fixture
def short_work_root():
    """Return a build root short enough to pass the Windows long-path guard, or skip."""
    root = Path(tempfile.mkdtemp(prefix="ur"))
    if len(str(root)) > 60:
        shutil.rmtree(root, ignore_errors=True)
        pytest.skip(f"TEMP path too long for the adapter build guard: {root}")
    yield root
    shutil.rmtree(root, ignore_errors=True)


def _windows_cfg(**overrides) -> ProvisionSettings:
    """Return a Windows configuration with a plain cmake command name."""
    return ProvisionSettings(platform="windows", cmake_exe="cmake", **overrides)


def _linux_cfg(**overrides) -> ProvisionSettings:
    """Return a Linux configuration with a plain cmake command name."""
    return ProvisionSettings(platform="linux", cmake_exe="cmake", **overrides)


def _build_dir_for(work_root: Path, vendor: str = "fake") -> Path:
    """Return the build directory the builder derives for *vendor* at :data:`_COMMIT`."""
    return work_root / f"{vendor}-{_COMMIT[:8]}"


def test_a_full_build_records_the_expected_argv_and_installs_binaries(
        tmp_path, short_work_root, recording_console):
    cfg = _windows_cfg()
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    work_root = short_work_root
    build_dir = _build_dir_for(work_root)

    runner = _FakeRunner(build_dir, ["ur_adapter_fake.dll"])
    builder = AdapterBuilder(cfg=cfg, runner=runner, work_root=work_root,
                             environment=lambda cfg: {})

    result = builder.build(_fake_spec(), install, toolchain_root, _COMMIT, dry_run=False)

    assert result is True
    assert (toolchain_root / "bin" / "ur_adapter_fake.dll").is_file()

    fetch_calls = [c for c in runner.calls if c[0] == "git"]
    assert [c[1] for c in fetch_calls] == [
        "init", "remote", "sparse-checkout", "fetch", "checkout"]
    assert fetch_calls[1] == ["git", "remote", "add", "origin",
                              "https://github.com/intel/llvm.git"]
    assert fetch_calls[2] == ["git", "sparse-checkout", "set", "--no-cone",
                              "/unified-runtime/"]
    assert fetch_calls[3][:4] == ["git", "fetch", "--depth", "1"]
    assert _COMMIT in fetch_calls[3]

    configure_call = next(c for c in runner.calls if "-S" in c)
    assert "-DUR_BUILD_ADAPTER_FAKE=ON" in configure_call
    assert "-DFAKE_ROOT=" + str(install.root) in configure_call
    assert "-DUR_BUILD_TESTS=OFF" in configure_call
    assert "-DCMAKE_C_COMPILER=cl" in configure_call
    assert "-DCMAKE_CXX_COMPILER=cl" in configure_call
    assert any(a.startswith("-DFETCHCONTENT_BASE_DIR=") and _COMMIT[:8] in a
              for a in configure_call)

    build_call = next(c for c in runner.calls if c[:2] == ["cmake", "--build"])
    assert "--target" in build_call
    assert build_call[build_call.index("--target") + 1] == "ur_adapter_fake"

    stamp = json.loads((toolchain_root / TOOLCHAIN_STAMP).read_text())
    assert stamp["adapters"]["fake"] == _COMMIT


def test_a_second_call_with_the_same_commit_is_skipped(
        tmp_path, short_work_root, recording_console):
    cfg = _windows_cfg()
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    work_root = short_work_root
    build_dir = _build_dir_for(work_root)

    runner = _FakeRunner(build_dir, ["ur_adapter_fake.dll"])
    builder = AdapterBuilder(cfg=cfg, runner=runner, work_root=work_root,
                             environment=lambda cfg: {})
    assert builder.build(_fake_spec(), install, toolchain_root, _COMMIT, dry_run=False)

    runner.calls.clear()
    again = builder.build(_fake_spec(), install, toolchain_root, _COMMIT, dry_run=False)

    assert again is True
    assert runner.calls == []


def test_a_matching_stamp_with_a_missing_binary_rebuilds(
        tmp_path, short_work_root, recording_console):
    cfg = _windows_cfg()
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    work_root = short_work_root
    build_dir = _build_dir_for(work_root)

    runner = _FakeRunner(build_dir, ["ur_adapter_fake.dll"])
    builder = AdapterBuilder(cfg=cfg, runner=runner, work_root=work_root,
                             environment=lambda cfg: {})
    assert builder.build(_fake_spec(), install, toolchain_root, _COMMIT, dry_run=False)

    (toolchain_root / "bin" / "ur_adapter_fake.dll").unlink()
    runner.calls.clear()
    shutil.rmtree(build_dir, ignore_errors=True)

    again = builder.build(_fake_spec(), install, toolchain_root, _COMMIT, dry_run=False)

    assert again is True
    assert runner.calls != []
    assert (toolchain_root / "bin" / "ur_adapter_fake.dll").is_file()


def test_a_dry_run_reports_and_runs_no_commands(tmp_path, short_work_root, recording_console):
    cfg = _windows_cfg()
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    work_root = short_work_root
    build_dir = _build_dir_for(work_root)

    runner = _FakeRunner(build_dir, ["ur_adapter_fake.dll"])
    builder = AdapterBuilder(cfg=cfg, runner=runner, work_root=work_root,
                             environment=lambda cfg: {})

    result = builder.build(_fake_spec(), install, toolchain_root, _COMMIT, dry_run=True)

    assert result is True
    assert runner.calls == []
    assert not (toolchain_root / TOOLCHAIN_STAMP).exists()


def test_a_failing_configure_returns_false_and_leaves_bin_untouched(
        tmp_path, short_work_root, recording_console):
    cfg = _windows_cfg()
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    work_root = short_work_root
    build_dir = _build_dir_for(work_root)

    runner = _FakeRunner(build_dir, ["ur_adapter_fake.dll"], fail_on="-S")
    builder = AdapterBuilder(cfg=cfg, runner=runner, work_root=work_root,
                             environment=lambda cfg: {})

    result = builder.build(_fake_spec(), install, toolchain_root, _COMMIT, dry_run=False)

    assert result is False
    assert not (toolchain_root / "bin").exists()
    assert not (toolchain_root / TOOLCHAIN_STAMP).exists()


def test_a_missing_git_or_cmake_returns_false_without_raising(
        tmp_path, short_work_root, recording_console):
    cfg = _windows_cfg()
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    work_root = short_work_root

    builder = AdapterBuilder(cfg=cfg, runner=_MissingExecutableRunner(), work_root=work_root,
                             environment=lambda cfg: {})

    result = builder.build(_fake_spec(), install, toolchain_root, _COMMIT, dry_run=False)

    assert result is False
    assert not (toolchain_root / "bin").exists()


def test_a_failing_install_rolls_back_every_binary_already_placed(
        tmp_path, short_work_root, monkeypatch, recording_console):
    cfg = _windows_cfg()
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    work_root = short_work_root
    build_dir = _build_dir_for(work_root)

    spec = _fake_spec(binary_bases=("ur_adapter_fake", "umf"))
    runner = _FakeRunner(build_dir, ["ur_adapter_fake.dll", "umf.dll"])
    builder = AdapterBuilder(cfg=cfg, runner=runner, work_root=work_root,
                             environment=lambda cfg: {})

    real_replace = os.replace
    calls = {"n": 0}

    def flaky_replace(src, dst):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("disk full")
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", flaky_replace)

    result = builder.build(spec, install, toolchain_root, _COMMIT, dry_run=False)

    assert result is False
    bin_dir = toolchain_root / "bin"
    remaining = list(bin_dir.glob("*.dll")) if bin_dir.is_dir() else []
    assert remaining == []
    assert not (toolchain_root / TOOLCHAIN_STAMP).exists()


def test_a_failing_install_restores_a_pre_existing_binary(
        tmp_path, short_work_root, monkeypatch, recording_console):
    cfg = _windows_cfg()
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    bin_dir = toolchain_root / "bin"
    bin_dir.mkdir()
    old_binary = bin_dir / "ur_adapter_fake.dll"
    old_binary.write_bytes(b"old")
    work_root = short_work_root
    build_dir = _build_dir_for(work_root)

    spec = _fake_spec(binary_bases=("ur_adapter_fake", "umf"))
    runner = _FakeRunner(build_dir, ["ur_adapter_fake.dll", "umf.dll"])
    builder = AdapterBuilder(cfg=cfg, runner=runner, work_root=work_root,
                             environment=lambda cfg: {})

    real_replace = os.replace
    calls = {"n": 0}

    def flaky_replace(src, dst):
        calls["n"] += 1
        # Let both "move existing aside" calls through, fail the second install.
        if calls["n"] == 3:
            raise OSError("disk full")
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", flaky_replace)

    result = builder.build(spec, install, toolchain_root, _COMMIT, dry_run=False)

    assert result is False
    assert old_binary.read_bytes() == b"old"
    assert not (bin_dir / "umf.dll").exists()
    assert not (toolchain_root / TOOLCHAIN_STAMP).exists()


def test_an_existing_stamp_keeps_its_source_and_tag_across_a_build(
        tmp_path, short_work_root, recording_console):
    cfg = _windows_cfg()
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    write_toolchain_stamp(toolchain_root, "intel/llvm", "nightly-2026-09-14")
    work_root = short_work_root
    build_dir = _build_dir_for(work_root)

    runner = _FakeRunner(build_dir, ["ur_adapter_fake.dll"])
    builder = AdapterBuilder(cfg=cfg, runner=runner, work_root=work_root,
                             environment=lambda cfg: {})

    builder.build(_fake_spec(), install, toolchain_root, _COMMIT, dry_run=False)

    stamp = json.loads((toolchain_root / TOOLCHAIN_STAMP).read_text())
    assert stamp["source"] == "intel/llvm"
    assert stamp["tag"] == "nightly-2026-09-14"
    assert stamp["adapters"]["fake"] == _COMMIT


def test_windows_maps_a_base_name_to_a_dll(tmp_path, short_work_root, recording_console):
    cfg = _windows_cfg()
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    work_root = short_work_root
    build_dir = _build_dir_for(work_root)

    runner = _FakeRunner(build_dir, ["ur_adapter_fake.dll"])
    builder = AdapterBuilder(cfg=cfg, runner=runner, work_root=work_root,
                             environment=lambda cfg: {})
    builder.build(_fake_spec(), install, toolchain_root, _COMMIT, dry_run=False)

    assert (toolchain_root / "bin" / "ur_adapter_fake.dll").is_file()
    assert not (toolchain_root / "lib").exists()


def test_linux_maps_a_base_name_to_a_versioned_shared_object(
        tmp_path, short_work_root, recording_console):
    cfg = _linux_cfg()
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    work_root = short_work_root
    build_dir = _build_dir_for(work_root)

    runner = _FakeRunner(build_dir, ["libur_adapter_fake.so.0"])
    builder = AdapterBuilder(cfg=cfg, runner=runner, work_root=work_root,
                             environment=lambda cfg: {})
    result = builder.build(_fake_spec(), install, toolchain_root, _COMMIT, dry_run=False)

    assert result is True
    assert (toolchain_root / "lib" / "libur_adapter_fake.so.0").is_file()
    assert not (toolchain_root / "bin").exists()


def test_linux_configure_does_not_force_the_msvc_compiler(
        tmp_path, short_work_root, recording_console):
    cfg = _linux_cfg()
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    work_root = short_work_root
    build_dir = _build_dir_for(work_root)

    runner = _FakeRunner(build_dir, ["libur_adapter_fake.so.0"])
    builder = AdapterBuilder(cfg=cfg, runner=runner, work_root=work_root,
                             environment=lambda cfg: {})
    builder.build(_fake_spec(), install, toolchain_root, _COMMIT, dry_run=False)

    configure_call = next(c for c in runner.calls if "-S" in c)
    assert "-DCMAKE_C_COMPILER=cl" not in configure_call
    assert "-DCMAKE_CXX_COMPILER=cl" not in configure_call


def test_configure_passes_ninja_from_config_when_set(
        tmp_path, short_work_root, recording_console):
    cfg = _windows_cfg(ninja_exe="ninja.exe")
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    work_root = short_work_root
    build_dir = _build_dir_for(work_root)

    runner = _FakeRunner(build_dir, ["ur_adapter_fake.dll"])
    builder = AdapterBuilder(cfg=cfg, runner=runner, work_root=work_root,
                             environment=lambda cfg: {})
    builder.build(_fake_spec(), install, toolchain_root, _COMMIT, dry_run=False)

    configure_call = next(c for c in runner.calls if "-S" in c)
    assert "-DCMAKE_MAKE_PROGRAM=ninja.exe" in configure_call


def test_configure_omits_ninja_program_when_not_configured(
        tmp_path, short_work_root, recording_console):
    cfg = _windows_cfg()
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    work_root = short_work_root
    build_dir = _build_dir_for(work_root)

    runner = _FakeRunner(build_dir, ["ur_adapter_fake.dll"])
    builder = AdapterBuilder(cfg=cfg, runner=runner, work_root=work_root,
                             environment=lambda cfg: {})
    builder.build(_fake_spec(), install, toolchain_root, _COMMIT, dry_run=False)

    configure_call = next(c for c in runner.calls if "-S" in c)
    assert not any(a.startswith("-DCMAKE_MAKE_PROGRAM=") for a in configure_call)


def test_the_environment_provider_is_called_at_most_once_per_builder(
        tmp_path, short_work_root, recording_console):
    cfg = _windows_cfg()
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    work_root = short_work_root

    calls = {"n": 0}

    def counting_environment(cfg):
        calls["n"] += 1
        return {}

    spec = _fake_spec()
    build_dir = _build_dir_for(work_root)
    runner = _FakeRunner(build_dir, ["ur_adapter_fake.dll"])
    builder = AdapterBuilder(cfg=cfg, runner=runner, work_root=work_root,
                             environment=counting_environment)

    builder.build(spec, install, toolchain_root, _COMMIT, dry_run=False)
    shutil.rmtree(build_dir)
    another_toolchain_root = tmp_path / "llvm-sycl-2"
    another_toolchain_root.mkdir()
    builder.build(spec, install, another_toolchain_root, _COMMIT, dry_run=False)

    assert calls["n"] == 1


def test_a_long_work_root_is_refused_on_windows(tmp_path, recording_console):
    cfg = _windows_cfg()
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir()
    long_root = tmp_path / ("x" * 80)

    runner = _FakeRunner(long_root / "build", ["ur_adapter_fake.dll"])
    builder = AdapterBuilder(cfg=cfg, runner=runner, work_root=long_root,
                             environment=lambda cfg: {})

    result = builder.build(_fake_spec(), install, toolchain_root, _COMMIT, dry_run=False)

    assert result is False
    assert runner.calls == []


def test_default_work_root_follows_the_dependency_root(provision_home, recording_console):
    cfg = _linux_cfg()
    builder = AdapterBuilder(cfg=cfg, runner=_MissingExecutableRunner())

    assert builder.work_root == provision_home.resolve() / "ur"
