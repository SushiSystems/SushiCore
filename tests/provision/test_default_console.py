# test_default_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the default console the deprecated ``bind_console`` sets."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.default_console import DEFAULT_CONSOLE, DefaultConsole, bind_console
from sushicore.provision.module_provision import ModuleProvision

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
