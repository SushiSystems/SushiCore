# test_default_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the default console the deprecated ``bind_console`` sets."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.default_console import (DEFAULT_CONSOLE, DefaultConsole, bind_console,
                                                 console_or_default)
from sushicore.provision.configure_step import ConfigureStep
from sushicore.provision.detect_step import DetectStep
from sushicore.provision.fragments import TomlDependencySource
from sushicore.provision.git_client import GitClient
from sushicore.provision.gpu.adapter_builder import AdapterBuilder, SubprocessBuildStepExecutor
from sushicore.provision.gpu_stage import GpuStage
from sushicore.provision.install_deps_step import InstallDepsStep
from sushicore.provision.module_provision import ModuleProvision
from sushicore.provision.packages.direct_download import DirectDownloadWindowsManager, downloader
from sushicore.provision.packages.linux import AptManager
from sushicore.provision.packages.winget import WingetManager
from sushicore.provision.pipeline import InstallPipeline
from sushicore.provision.process_run import provision_runner
from sushicore.provision.sushi_fetch import FetchSushiSourcesStep
from sushicore.provision.uninstall_step import UninstallStep

pytestmark = pytest.mark.small


def test_a_bound_provider_is_called_on_each_use():
    """Check that the default console returns what its provider returns, every time."""
    recording = RecordingConsole()
    default = DefaultConsole()
    default.bind(lambda: recording)
    assert default() is recording


def test_an_unbound_default_raises_a_named_error():
    """Check that a default with no provider tells the caller to pass a console."""
    with pytest.raises(RuntimeError, match="console="):
        DefaultConsole()()


def test_unbinding_takes_the_console_away():
    """Check that binding None removes the provider."""
    default = DefaultConsole()
    default.bind(lambda: RecordingConsole())
    default.bind(None)
    with pytest.raises(RuntimeError, match="console="):
        default()


def test_binding_does_not_call_the_provider():
    """Check that a provider stays lazy until the console is used."""
    asked = []
    DefaultConsole().bind(lambda: asked.append("asked"))
    assert asked == []


def test_bind_console_warns_that_it_is_deprecated():
    """Check that the shim announces its removal."""
    with pytest.warns(DeprecationWarning, match="bind_console"):
        bind_console(None)


def test_a_module_provision_without_a_console_uses_the_one_bind_console_set():
    """Check that the shim sets the console of a ModuleProvision that names none."""
    recording = RecordingConsole()
    with pytest.warns(DeprecationWarning):
        bind_console(lambda: recording)
    try:
        module = ModuleProvision(profile=None, project_root=None, load_config=None)
        assert module.console() is recording
    finally:
        DEFAULT_CONSOLE.bind(None)


@pytest.fixture
def default_console():
    """Bind a recording console as the default one, and unbind it afterwards."""
    recording = RecordingConsole()
    DEFAULT_CONSOLE.bind(lambda: recording)
    yield recording
    DEFAULT_CONSOLE.bind(None)


def test_a_console_that_is_given_is_returned_without_a_warning(recwarn):
    """Check that the given console passes through and nothing warns."""
    recording = RecordingConsole()
    assert (console_or_default(recording, "Thing"), len(recwarn)) == (recording, 0)


def test_a_missing_console_warns_naming_the_owner_and_pointing_at_the_frame_depth_names():
    """Check that the warning names the owner and the file that the depth counts to."""
    with pytest.warns(DeprecationWarning, match="Thing without console=") as caught:
        console_or_default(None, "Thing", depth=1)
    assert caught[0].filename == __file__


def test_the_default_is_read_when_it_is_used_not_when_it_is_resolved(default_console):
    """Check that a console bound after the resolve still receives the call."""
    DEFAULT_CONSOLE.bind(None)
    with pytest.warns(DeprecationWarning):
        resolved = console_or_default(None, "Thing")
    DEFAULT_CONSOLE.bind(lambda: default_console)
    resolved.info("hello")
    assert default_console.texts("info") == ["hello"]


def test_using_a_default_nothing_has_bound_raises_the_named_error():
    """Check that an unbound default fails when used, with the instruction to pass a console."""
    with pytest.warns(DeprecationWarning):
        resolved = console_or_default(None, "Thing")
    with pytest.raises(RuntimeError, match="console="):
        resolved.info("hello")


K_BUILDERS = {
    "ConfigureStep": lambda **kw: ConfigureStep(object(), **kw),
    "DetectStep": lambda **kw: DetectStep(object(), **kw),
    "TomlDependencySource": lambda **kw: TomlDependencySource([], **kw),
    "GitClient": lambda **kw: GitClient(**kw),
    "SubprocessBuildStepExecutor": lambda **kw: SubprocessBuildStepExecutor(**kw),
    "AdapterBuilder": lambda **kw: AdapterBuilder(object(), object(), **kw),
    "GpuStage": lambda **kw: GpuStage(**kw),
    "InstallDepsStep": lambda **kw: InstallDepsStep(object(), [], **kw),
    "DirectDownloadWindowsManager": lambda **kw: DirectDownloadWindowsManager(**kw),
    "downloader": lambda **kw: downloader(**kw),
    "AptManager": lambda **kw: AptManager(**kw),
    "WingetManager": lambda **kw: WingetManager(**kw),
    "InstallPipeline": lambda **kw: InstallPipeline([], **kw),
    "provision_runner": lambda **kw: provision_runner(**kw),
    "FetchSushiSourcesStep": lambda **kw: FetchSushiSourcesStep(Path("."), [], object(), **kw),
    "UninstallStep": lambda **kw: UninstallStep(object(), [], object(), **kw),
}


@pytest.mark.parametrize("name", sorted(K_BUILDERS))
def test_building_without_a_console_warns_and_points_at_the_caller(name):
    """Check that the omitted console is a deprecation warning at this file, not an error."""
    with pytest.warns(DeprecationWarning, match="console=") as caught:
        K_BUILDERS[name]()
    assert caught[0].filename == __file__


@pytest.mark.parametrize("name", sorted(K_BUILDERS))
def test_building_with_a_console_warns_of_nothing(name, recwarn):
    """Check that a caller that passes its console sees no deprecation warning."""
    K_BUILDERS[name](console=RecordingConsole())
    assert [w for w in recwarn if issubclass(w.category, DeprecationWarning)] == []
