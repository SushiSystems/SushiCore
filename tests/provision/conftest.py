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
