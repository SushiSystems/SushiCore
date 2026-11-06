# test_adapter_builder.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The adapter builder fetches, configures, builds and stamps a Unified Runtime adapter."""

from __future__ import annotations

import dataclasses
import json
import logging
import os
import shutil
import tempfile
import typing
from pathlib import Path

import pytest

from sushicore.provision import home
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.gpu.adapter_builder import AdapterBuilder
from sushicore.provision.gpu.adapter_builder_memory import InMemoryCommandRunner
from sushicore.provision.toolchains.stamp import TOOLCHAIN_STAMP

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


class _CountedReplace:
    """Renames files like :func:`os.replace`, but raises on the call numbered *fail_on*."""

    def __init__(self, fail_on: int) -> None:
        """Count calls from one, and fail the one numbered *fail_on*."""
        self._fail_on = fail_on
        self._count = 0

    def __call__(self, source: Path, destination: Path) -> None:
        """Rename *source* to *destination*, or raise :class:`OSError` on the failing call."""
        self._count += 1
        if self._count == self._fail_on:
            raise OSError("disk full")
        os.replace(source, destination)


class _LockedPreviousCopies:
    """Deletes files like :meth:`pathlib.Path.unlink`, but refuses a ``.previous`` copy."""

    def __call__(self, path: Path) -> None:
        """Delete *path*, or raise :class:`PermissionError` for a ``.previous`` copy."""
        if path.name.endswith(".previous"):
            raise PermissionError(13, "file is in use", str(path))
        path.unlink()


class _ListHandler(logging.Handler):
    """Keeps the formatted message of every record it receives."""

    def __init__(self) -> None:
        """Start with no messages."""
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Keep the message of *record*."""
        self.messages.append(record.getMessage())


@dataclasses.dataclass
class _Scene:
    """What one build holds: the runner, the builder, the places it touches and its result."""

    result: bool
    runner: InMemoryCommandRunner
    builder: AdapterBuilder
    toolchain_root: Path
    work_root: Path
    install: _ToolkitInstall


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


def _produce(work_root: Path, names: list[str]) -> None:
    """Write the files a successful cmake build leaves in the build directory of :data:`_COMMIT`."""
    output_dir = work_root / f"fake-{_COMMIT[:8]}" / "bin"
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        (output_dir / name).write_bytes(b"fake")


def _builder(tmp_path: Path, work_root: Path, *, cfg: ProvisionSettings | None = None,
             runner: InMemoryCommandRunner | None = None, **seams) -> _Scene:
    """Return a scene that holds a builder over *runner* and a fresh toolchain folder, not yet run."""
    toolchain_root = tmp_path / "llvm-sycl"
    toolchain_root.mkdir(exist_ok=True)
    chosen = runner or InMemoryCommandRunner()
    builder = AdapterBuilder(cfg=cfg or _windows_cfg(), runner=chosen, work_root=work_root,
                             environment=lambda cfg: {}, **seams)
    install = _ToolkitInstall(root=tmp_path / "toolkit", version="1.0")
    return _Scene(False, chosen, builder, toolchain_root, work_root, install)


def _run(scene: _Scene, spec: _GpuBackendSpec | None = None, *, dry_run: bool = False) -> _Scene:
    """Build once in *scene* and record the result in it."""
    scene.result = scene.builder.build(spec or _fake_spec(), scene.install, scene.toolchain_root,
                                       _COMMIT, dry_run=dry_run)
    return scene


def _configure_call(scene: _Scene) -> list[str]:
    """Return the cmake configure command the scene's runner recorded."""
    return next(c for c in scene.runner.calls if "-S" in c)


@pytest.mark.medium
def test_a_build_fetches_the_sources_with_a_sparse_checkout_of_the_commit(
        tmp_path, short_work_root, recording_console):
    """Check that a build fetches only unified-runtime at the commit, in five git steps."""
    _produce(short_work_root, ["ur_adapter_fake.dll"])

    scene = _run(_builder(tmp_path, short_work_root))

    fetch_calls = [c for c in scene.runner.calls if c[0] == "git"]
    assert fetch_calls == [
        ["git", "init"],
        ["git", "remote", "add", "origin", "https://github.com/intel/llvm.git"],
        ["git", "sparse-checkout", "set", "--no-cone", "/unified-runtime/"],
        ["git", "fetch", "--depth", "1", "--filter=blob:none", "origin", _COMMIT],
        ["git", "checkout", "FETCH_HEAD"],
    ]


@pytest.mark.medium
def test_a_build_configures_the_adapter_option_and_the_toolkit_definitions(
        tmp_path, short_work_root, recording_console):
    """Check that the configure command enables the adapter and passes the vendor definitions."""
    _produce(short_work_root, ["ur_adapter_fake.dll"])

    scene = _run(_builder(tmp_path, short_work_root))

    configure_call = _configure_call(scene)
    assert "-DUR_BUILD_ADAPTER_FAKE=ON" in configure_call
    assert "-DFAKE_ROOT=" + str(scene.install.root) in configure_call
    assert "-DUR_BUILD_TESTS=OFF" in configure_call
    assert any(a.startswith("-DFETCHCONTENT_BASE_DIR=") and _COMMIT[:8] in a
               for a in configure_call)


@pytest.mark.medium
def test_a_windows_configure_forces_the_msvc_compiler(
        tmp_path, short_work_root, recording_console):
    """Check that a Windows configure names cl as the C and C++ compiler."""
    _produce(short_work_root, ["ur_adapter_fake.dll"])

    scene = _run(_builder(tmp_path, short_work_root))

    configure_call = _configure_call(scene)
    assert "-DCMAKE_C_COMPILER=cl" in configure_call
    assert "-DCMAKE_CXX_COMPILER=cl" in configure_call


@pytest.mark.medium
def test_a_build_runs_cmake_on_the_adapter_target(tmp_path, short_work_root, recording_console):
    """Check that the build step names the vendor's adapter target."""
    _produce(short_work_root, ["ur_adapter_fake.dll"])

    scene = _run(_builder(tmp_path, short_work_root))

    build_call = next(c for c in scene.runner.calls if c[:2] == ["cmake", "--build"])
    assert build_call[build_call.index("--target") + 1] == "ur_adapter_fake"


@pytest.mark.medium
def test_a_full_build_installs_the_binaries_into_the_toolchain(
        tmp_path, short_work_root, recording_console):
    """Check that a full build returns True and places the DLL under the toolchain's bin."""
    _produce(short_work_root, ["ur_adapter_fake.dll"])

    scene = _run(_builder(tmp_path, short_work_root))

    assert scene.result is True
    assert (scene.toolchain_root / "bin" / "ur_adapter_fake.dll").is_file()


@pytest.mark.medium
def test_a_full_build_stamps_the_commit_for_the_vendor(
        tmp_path, short_work_root, recording_console):
    """Check that a full build records the built commit under the vendor in the stamp."""
    _produce(short_work_root, ["ur_adapter_fake.dll"])

    scene = _run(_builder(tmp_path, short_work_root))

    stamp = json.loads((scene.toolchain_root / TOOLCHAIN_STAMP).read_text())
    assert stamp["adapters"]["fake"] == _COMMIT


@pytest.mark.medium
def test_a_second_call_with_the_same_commit_is_skipped(
        tmp_path, short_work_root, recording_console):
    """Check that a second call with the same commit runs no command."""
    _produce(short_work_root, ["ur_adapter_fake.dll"])
    scene = _run(_builder(tmp_path, short_work_root))
    scene.runner.calls.clear()

    again = _run(scene)

    assert again.result is True
    assert again.runner.calls == []


@pytest.mark.medium
def test_a_matching_stamp_with_a_missing_binary_rebuilds(
        tmp_path, short_work_root, recording_console):
    """Check that a stamp for the commit does not skip the build when a binary is gone."""
    _produce(short_work_root, ["ur_adapter_fake.dll"])
    scene = _run(_builder(tmp_path, short_work_root))
    (scene.toolchain_root / "bin" / "ur_adapter_fake.dll").unlink()
    scene.runner.calls.clear()

    again = _run(scene)

    assert again.result is True
    assert again.runner.calls != []
    assert (scene.toolchain_root / "bin" / "ur_adapter_fake.dll").is_file()


@pytest.mark.medium
def test_a_dry_run_runs_no_commands_and_writes_no_stamp(
        tmp_path, short_work_root, recording_console):
    """Check that a dry run returns True, runs nothing and leaves no stamp."""
    scene = _run(_builder(tmp_path, short_work_root), dry_run=True)

    assert scene.result is True
    assert scene.runner.calls == []
    assert not (scene.toolchain_root / TOOLCHAIN_STAMP).exists()


@pytest.mark.medium
def test_a_dry_run_says_which_adapter_it_would_build(
        tmp_path, short_work_root, recording_console):
    """Check that a dry run prints one line naming the vendor and the short commit."""
    _run(_builder(tmp_path, short_work_root), dry_run=True)

    assert recording_console.texts("info") == [
        f"(dry-run) would build fake adapter at {_COMMIT[:12]}"]


@pytest.mark.medium
def test_a_failing_configure_returns_false_and_leaves_bin_untouched(
        tmp_path, short_work_root, recording_console):
    """Check that a failing configure returns False, installs nothing and writes no stamp."""
    _produce(short_work_root, ["ur_adapter_fake.dll"])
    runner = InMemoryCommandRunner(fail_on="-S")

    scene = _run(_builder(tmp_path, short_work_root, runner=runner))

    assert scene.result is False
    assert not (scene.toolchain_root / "bin").exists()
    assert not (scene.toolchain_root / TOOLCHAIN_STAMP).exists()


@pytest.mark.medium
def test_a_missing_git_or_cmake_returns_false_without_raising(
        tmp_path, short_work_root, recording_console):
    """Check that an executable that is on no PATH fails the build instead of raising."""
    runner = InMemoryCommandRunner(missing=True)

    scene = _run(_builder(tmp_path, short_work_root, runner=runner))

    assert scene.result is False
    assert not (scene.toolchain_root / "bin").exists()


@pytest.mark.medium
def test_a_failing_install_rolls_back_every_binary_already_placed(
        tmp_path, short_work_root, recording_console):
    """Check that a rename that fails after one binary landed leaves bin without either binary."""
    _produce(short_work_root, ["ur_adapter_fake.dll", "umf.dll"])
    scene = _builder(tmp_path, short_work_root, replace=_CountedReplace(fail_on=2))

    _run(scene, _fake_spec(binary_bases=("ur_adapter_fake", "umf")))

    assert scene.result is False
    assert list((scene.toolchain_root / "bin").glob("*.dll")) == []
    assert not (scene.toolchain_root / TOOLCHAIN_STAMP).exists()


@pytest.mark.medium
def test_a_failing_install_restores_a_pre_existing_binary(
        tmp_path, short_work_root, recording_console):
    """Check that a failing install puts the old binary back and removes the new one."""
    _produce(short_work_root, ["ur_adapter_fake.dll", "umf.dll"])
    scene = _builder(tmp_path, short_work_root, replace=_CountedReplace(fail_on=3))
    bin_dir = scene.toolchain_root / "bin"
    bin_dir.mkdir()
    (bin_dir / "ur_adapter_fake.dll").write_bytes(b"old")

    _run(scene, _fake_spec(binary_bases=("ur_adapter_fake", "umf")))

    assert scene.result is False
    assert (bin_dir / "ur_adapter_fake.dll").read_bytes() == b"old"
    assert not (bin_dir / "umf.dll").exists()


@pytest.mark.medium
@pytest.mark.parametrize(("cfg", "built", "folder", "other"), [
    (_windows_cfg(), "ur_adapter_fake.dll", "bin", "lib"),
    (_linux_cfg(), "libur_adapter_fake.so.0", "lib", "bin"),
], ids=["windows-dll", "linux-versioned-so"])
def test_a_base_name_maps_to_the_platforms_file_and_folder(
        tmp_path, short_work_root, recording_console, cfg, built, folder, other):
    """Check that the platform picks the binary's file name and the toolchain folder it lands in."""
    _produce(short_work_root, [built])

    scene = _run(_builder(tmp_path, short_work_root, cfg=cfg))

    assert scene.result is True
    assert (scene.toolchain_root / folder / built).is_file()
    assert not (scene.toolchain_root / other).exists()


@pytest.mark.medium
def test_linux_configure_does_not_force_the_msvc_compiler(
        tmp_path, short_work_root, recording_console):
    """Check that a Linux configure names no cl compiler."""
    _produce(short_work_root, ["libur_adapter_fake.so.0"])

    scene = _run(_builder(tmp_path, short_work_root, cfg=_linux_cfg()))

    configure_call = _configure_call(scene)
    assert "-DCMAKE_C_COMPILER=cl" not in configure_call
    assert "-DCMAKE_CXX_COMPILER=cl" not in configure_call


@pytest.mark.medium
@pytest.mark.parametrize(("ninja_exe", "expected"), [
    ("ninja.exe", ["-DCMAKE_MAKE_PROGRAM=ninja.exe"]),
    ("", []),
], ids=["configured", "not-configured"])
def test_configure_passes_the_configured_ninja_program_only(
        tmp_path, short_work_root, recording_console, ninja_exe, expected):
    """Check that the make program is passed when ninja is configured and omitted when not."""
    _produce(short_work_root, ["ur_adapter_fake.dll"])

    scene = _run(_builder(tmp_path, short_work_root, cfg=_windows_cfg(ninja_exe=ninja_exe)))

    passed = [a for a in _configure_call(scene) if a.startswith("-DCMAKE_MAKE_PROGRAM=")]
    assert passed == expected


@pytest.mark.medium
def test_the_environment_provider_is_called_at_most_once_per_builder(
        tmp_path, short_work_root, recording_console):
    """Check that two builds on one builder ask for the environment once."""
    _produce(short_work_root, ["ur_adapter_fake.dll"])
    asked: list[object] = []
    scene = _builder(tmp_path, short_work_root)
    scene.builder.environment = lambda cfg: asked.append(cfg) or {}
    _run(scene)
    other = tmp_path / "llvm-sycl-2"
    other.mkdir()
    scene.toolchain_root = other

    _run(scene)

    assert len(asked) == 1


@pytest.mark.medium
def test_a_long_work_root_is_refused_on_windows(tmp_path, recording_console):
    """Check that a work root over the limit fails the build before any command runs."""
    scene = _run(_builder(tmp_path, tmp_path / ("x" * 80)))

    assert scene.result is False
    assert scene.runner.calls == []


@pytest.mark.small
def test_the_default_work_root_is_ur_under_the_dependency_root():
    """Check that build trees go under ``ur`` in the root the dependency root is bound to."""
    root = Path("dependency-root")
    home.bind_root(lambda: root)
    try:
        builder = AdapterBuilder(cfg=_linux_cfg(), runner=InMemoryCommandRunner())
    finally:
        home.bind_root(None)

    assert builder.work_root == root.resolve() / "ur"


@pytest.mark.medium
def test_a_previous_binary_that_cannot_be_removed_is_recorded(
        tmp_path, short_work_root, recording_console):
    """Check that a leftover ``.previous`` copy is logged and the install still succeeds."""
    _produce(short_work_root, ["ur_adapter_fake.dll"])
    handler = _ListHandler()
    logger = logging.Logger("adapter-builder-test")
    logger.addHandler(handler)
    scene = _builder(tmp_path, short_work_root, unlink=_LockedPreviousCopies(), log=logger)
    bin_dir = scene.toolchain_root / "bin"
    bin_dir.mkdir()
    (bin_dir / "ur_adapter_fake.dll").write_bytes(b"old")

    _run(scene)

    assert scene.result is True
    assert (bin_dir / "ur_adapter_fake.dll").read_bytes() == b"fake"
    assert len(handler.messages) == 1
    assert "ur_adapter_fake.dll.previous" in handler.messages[0]
