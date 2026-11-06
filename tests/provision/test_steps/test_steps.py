# test_steps.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the seams the shared steps gained."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.errors import DigestMismatchError
from sushicore.provision import download_verifier, steps
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.fragments import Dependency
from sushicore.provision.fragments_memory import InMemoryDependencySource
from sushicore.provision.packages import IPackageManager
from sushicore.provision.pipeline import InstallContext, InstallPipeline, StepResult
from sushicore.provision.sinks_memory import InMemoryConfigSink


def _actions(*, paths=None, **overrides) -> steps.MachineActions:
    """Build machine calls that touch nothing and probe *paths*, with *overrides* applied."""
    return steps.MachineActions(**{
        "refresh_path": lambda: None,
        "resolve_config": lambda cfg, gpu=False: dict(paths or {}),
        **overrides})


def _context(**overrides) -> InstallContext:
    """Build an install context for a Linux run with *overrides* applied."""
    return InstallContext(cfg=ProvisionSettings(platform="linux"), **overrides)


@pytest.mark.small
def test_configure_writes_through_the_sink():
    """Check that ConfigureStep hands the probed paths and the active toolchain to its sink."""
    sink = InMemoryConfigSink()
    step = steps.ConfigureStep(sink, console=RecordingConsole(),
                               actions=_actions(paths={"ninja_exe": "n"}))

    result = step.run(_context(active_toolchain="intel-llvm"))

    assert (result, sink.paths, sink.tool) == (
        StepResult.OK, [("linux", {"ninja_exe": "n"})], [{"toolchain": "intel-llvm"}])


@pytest.mark.small
def test_configure_backs_up_before_writing():
    """Check that the sink is asked for a backup before it is asked to write."""
    sink = InMemoryConfigSink(backup_path=Path("stub.toml.bak"))
    out = RecordingConsole()

    steps.ConfigureStep(sink, console=out, actions=_actions(paths={"ninja_exe": "n"})).run(_context())

    assert sink.calls == ["backup", "write_paths"]
    assert "Backed up existing config to stub.toml.bak" in out.texts("info")


@pytest.mark.small
def test_configure_skips_the_backup_line_when_there_is_nothing_to_back_up():
    """Check that no backup line is printed when the sink had no file to back up."""
    sink = InMemoryConfigSink(backup_path=None)
    out = RecordingConsole()

    steps.ConfigureStep(sink, console=out, actions=_actions(paths={"ninja_exe": "n"})).run(_context())

    assert not any(text.startswith("Backed up") for text in out.texts("info"))


@pytest.mark.small
def test_configure_dry_run_prints_the_rendered_config():
    """Check that a dry run prints the config it would write and touches the sink not at all."""
    sink = InMemoryConfigSink()
    out = RecordingConsole()
    step = steps.ConfigureStep(sink, console=out, actions=_actions(paths={"ninja_exe": "n"}))

    result = step.run(_context(dry_run=True))

    assert result is StepResult.OK
    assert any('ninja_exe = "n"' in text for text in out.texts("console.print"))
    assert sink.calls == []


@pytest.mark.medium
def test_uninstall_leaves_a_refused_root_intact(tmp_path, monkeypatch):
    """Check that a root which is the working directory is refused and left untouched."""
    monkeypatch.chdir(tmp_path)
    sentinel = tmp_path / "marker.txt"
    sentinel.write_text("keep me", encoding="utf-8")
    out = RecordingConsole()
    step = steps.UninstallStep(InMemoryDependencySource([]), managers=[],
                               sink=InMemoryConfigSink(), console=out, root=lambda: tmp_path)

    result = step.run(_context(everything=True))

    assert result is StepResult.FAILED
    assert sentinel.is_file()
    assert any(str(tmp_path) in text for text in out.texts("error"))


@pytest.mark.medium
def test_windows_uninstall_refuses_before_touching_tools(tmp_path):
    """Check that a refused root stops the Windows uninstall before any tool or config is removed."""
    root = tmp_path / "checkout"
    (root / ".git").mkdir(parents=True)
    cmake = root / "tools" / "cmake"
    doxygen = root / "tools" / "doxygen"
    cmake.mkdir(parents=True)
    doxygen.mkdir(parents=True)
    (root / "tools" / "ninja.exe").write_text("", encoding="utf-8")
    sink = InMemoryConfigSink()
    step = steps.UninstallStep(InMemoryDependencySource([]), managers=[], sink=sink,
                               console=RecordingConsole(), root=lambda: root)

    result = step.run(InstallContext(cfg=ProvisionSettings(platform="windows")))

    assert result is StepResult.FAILED
    assert cmake.is_dir() and doxygen.is_dir() and (root / "tools" / "ninja.exe").is_file()
    assert sink.calls == []


@pytest.mark.medium
def test_linux_uninstall_refuses_before_removing_anything(tmp_path):
    """Check that a refused root stops the Linux uninstall before the config is cleared."""
    root = tmp_path / "checkout"
    (root / ".git").mkdir(parents=True)
    sink = InMemoryConfigSink()
    step = steps.UninstallStep(InMemoryDependencySource([]), managers=[], sink=sink,
                               console=RecordingConsole(), root=lambda: root)

    result = step.run(_context())

    assert result is StepResult.FAILED
    assert sink.calls == []


def _rerun_hint(ctx: InstallContext) -> str:
    """Report an inventory with one missing component through *ctx*; return everything printed."""
    out = RecordingConsole()
    rows = [("ninja", "MISSING", "shared", "not found")]
    steps.DetectStep(InMemoryDependencySource([]), console=out).report_inventory(ctx, rows)
    return "\n".join(out.texts("info"))


@pytest.mark.small
def test_missing_dependency_hint_names_the_calling_program():
    """Assert the re-run hint names the program in the context, not hub."""
    hint = _rerun_hint(_context(program="st"))
    assert "`st setup`" in hint
    assert "hub install" not in hint


@pytest.mark.small
def test_missing_dependency_hint_uses_the_rerun_command_the_consumer_names():
    """Assert a consumer that names its own re-run command is quoted, whatever its program is called."""
    assert "`hub install`" in _rerun_hint(_context(program="hub", rerun_command="hub install"))


@pytest.mark.small
def test_a_context_names_no_consumer_until_it_is_given_one():
    """Assert the shared code carries no default consumer: with no program the hint is the bare setup."""
    hint = _rerun_hint(_context())
    assert "hub" not in hint
    assert "`setup`" in hint


class _DownloadingManager(IPackageManager):
    """A direct-download manager whose install verifies one downloaded archive."""

    name = "direct-download"

    def __init__(self, archive: Path, on_mismatch) -> None:
        """Verify *archive* on install, passing a mismatch to *on_mismatch*."""
        self._archive = archive
        self._on_mismatch = on_mismatch

    def available(self) -> bool:
        """Report present."""
        return True

    def is_installed(self, pkg: str) -> bool:
        """Report every package as missing."""
        return False

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Verify the archive as a download site does, and report success."""
        self._archive.write_bytes(b"not the pinned archive")
        try:
            download_verifier.verify_download("cmake", self._archive)
        except DigestMismatchError as error:
            self._on_mismatch(error)
        return True


def _install_step(manager: IPackageManager) -> steps.InstallDepsStep:
    """Build a Windows install step that pins cmake's digest and installs through *manager*."""
    source = InMemoryDependencySource([Dependency(name="cmake", sha256={"windows": "3f" * 32})])
    actions = _actions(which=lambda name: "/bin/git" if name == "git" else None,
                       find_vcvars=lambda: Path("vcvars64.bat"),
                       install_oneapi=lambda run: True)
    return steps.InstallDepsStep(source, managers=[manager], console=RecordingConsole(),
                                 actions=actions)


@pytest.mark.medium
def test_install_deps_binds_the_manifest_digests_for_the_length_of_the_run(tmp_path):
    """Check that the downloads of a run are verified against its fragments and no later."""
    archive = tmp_path / "cmake.zip"
    mismatches = []
    step = _install_step(_DownloadingManager(archive, mismatches.append))

    result = step.run(InstallContext(cfg=ProvisionSettings(platform="windows")))

    assert result is StepResult.OK
    assert len(mismatches) == 1
    download_verifier.verify_download("cmake", archive)


@pytest.mark.medium
def test_a_digest_mismatch_stops_the_pipeline_and_unbinds_the_run(tmp_path, recording_console):
    """Check that a mismatch leaves the pipeline as the error and later steps do not run."""
    archive = tmp_path / "cmake.zip"

    def raise_it(error):
        """Let the mismatch leave the install."""
        raise error

    later_sink = InMemoryConfigSink()
    later = steps.ConfigureStep(later_sink, console=RecordingConsole(),
                                actions=_actions(paths={"ninja_exe": "n"}))
    pipeline = InstallPipeline([_install_step(_DownloadingManager(archive, raise_it)), later])

    with pytest.raises(DigestMismatchError):
        pipeline.run(InstallContext(cfg=ProvisionSettings(platform="windows")), show_progress=False)

    assert later_sink.calls == []
    download_verifier.verify_download("cmake", archive)


@pytest.mark.small
@pytest.mark.parametrize(("hint", "expected"), [
    ("(`hub remove --all` does it for you).",
     "Remove the whole install by deleting that folder. (`hub remove --all` does it for you)."),
    ("", "Remove the whole install by deleting that folder."),
])
def test_the_removal_note_ends_with_the_hint_the_consumer_supplies_or_stands_alone(hint, expected):
    """Check that removal_note appends the consumer's hint, and leaves the plain note without one."""
    assert steps.removal_note(_context(program="hub", removal_hint=hint)) == expected
