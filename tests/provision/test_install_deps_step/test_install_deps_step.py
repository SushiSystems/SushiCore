# test_install_deps_step.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""How the install step binds the manifest digests for the length of a run."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.deps_fragment import Download
from sushicore.console_memory import RecordingConsole
from sushicore.errors import DigestMismatchError
from sushicore.provision import download_verifier
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.configure_step import ConfigureStep
from sushicore.provision.fragments import Dependency
from sushicore.provision.fragments_memory import InMemoryDependencySource
from sushicore.provision.install_deps_step import InstallDepsStep
from sushicore.provision.packages import IPackageManager
from sushicore.provision.packages.base_memory import InMemoryPackageManager
from sushicore.provision.install_context import InstallContext
from sushicore.provision.pipeline import InstallPipeline
from sushicore.provision.step_result import StepResult
from sushicore.provision.sinks_memory import InMemoryConfigSink
from sushicore.provision.machine_actions import MachineActions


def _actions(*, paths=None, **overrides) -> MachineActions:
    """Build machine calls that touch nothing and probe *paths*, with *overrides* applied."""
    return MachineActions(**{
        "refresh_path": lambda: None,
        "resolve_config": lambda cfg, gpu=False: dict(paths or {}),
        **overrides})


def _downloading_manager(archive: Path, on_mismatch) -> IPackageManager:
    """Build a direct-download manager whose install verifies one downloaded archive."""
    def download(pkgs: list[str], dry_run: bool) -> None:
        """Verify the archive as a download site does, passing a mismatch to *on_mismatch*."""
        archive.write_bytes(b"not the pinned archive")
        try:
            download_verifier.verify_download("cmake", archive)
        except DigestMismatchError as error:
            on_mismatch(error)

    return InMemoryPackageManager(name="direct-download", on_install=download)


def _install_step(manager: IPackageManager) -> InstallDepsStep:
    """Build a Windows install step that pins cmake's digest and installs through *manager*."""
    source = InMemoryDependencySource([Dependency(name="cmake", sha256={"windows": "3f" * 32})])
    actions = _actions(which=lambda name: "/bin/git" if name == "git" else None,
                       find_vcvars=lambda: Path("vcvars64.bat"),
                       install_oneapi=lambda run, console: True)
    return InstallDepsStep(source, managers=[manager], console=RecordingConsole(),
                                 actions=actions)


@pytest.mark.medium
def test_install_deps_binds_the_manifest_digests_for_the_length_of_the_run(tmp_path):
    """Check that the downloads of a run are verified against its fragments and no later."""
    archive = tmp_path / "cmake.zip"
    mismatches = []
    step = _install_step(_downloading_manager(archive, mismatches.append))

    result = step.run(InstallContext(cfg=ProvisionSettings(platform="windows")))

    assert result is StepResult.OK
    assert len(mismatches) == 1
    download_verifier.verify_download("cmake", archive)


@pytest.mark.medium
def test_install_deps_binds_the_pinned_downloads_of_the_run():
    """Check that an installer inside the run reads the download its fragment pins."""
    pinned = Download("cmake", "v1", "https://example.invalid/c.zip", "3f" * 32)
    seen = []
    manager = InMemoryPackageManager(
        name="direct-download",
        on_install=lambda pkgs, dry_run: seen.append(download_verifier.pinned_download("cmake")))
    source = InMemoryDependencySource([
        Dependency(name="cmake", version="v1", url={"windows": pinned.url},
                   sha256={"windows": pinned.sha256})])
    actions = _actions(which=lambda name: "/bin/git" if name == "git" else None,
                       find_vcvars=lambda: Path("vcvars64.bat"),
                       install_oneapi=lambda run, console: True)
    step = InstallDepsStep(source, managers=[manager], console=RecordingConsole(),
                           actions=actions)

    step.run(InstallContext(cfg=ProvisionSettings(platform="windows")))

    assert seen == [pinned]


@pytest.mark.medium
def test_a_digest_mismatch_stops_the_pipeline_and_unbinds_the_run(tmp_path, recording_console):
    """Check that a mismatch leaves the pipeline as the error and later steps do not run."""
    archive = tmp_path / "cmake.zip"

    def raise_it(error):
        """Let the mismatch leave the install."""
        raise error

    later_sink = InMemoryConfigSink()
    later = ConfigureStep(later_sink, console=RecordingConsole(),
                                actions=_actions(paths={"ninja_exe": "n"}))
    pipeline = InstallPipeline([_install_step(_downloading_manager(archive, raise_it)), later],
                               console=recording_console)

    with pytest.raises(DigestMismatchError):
        pipeline.run(InstallContext(cfg=ProvisionSettings(platform="windows")), show_progress=False)

    assert later_sink.calls == []
    download_verifier.verify_download("cmake", archive)
