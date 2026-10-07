# conftest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Shared fixtures for the whole suite."""

import pytest
from rich.color import Color
from rich.style import Style

from sushicore.provision import home


def _clear_caches(owner: type) -> None:
    """Clear every functools cache on ``owner``."""
    for name in dir(owner):
        clear = getattr(getattr(owner, name, None), "cache_clear", None)
        if clear is not None:
            clear()


@pytest.fixture(autouse=True)
def _leave_the_real_console_alone(monkeypatch):
    """Replace the virtual terminal switch, so no test changes the console it runs in."""
    monkeypatch.setattr(
        "sushicore.windows_console.enable_virtual_terminal", lambda *args, **kwargs: False,
    )


@pytest.fixture(autouse=True)
def _no_machine_dependency_root(tmp_path, monkeypatch):
    """Point ``SUSHISYSTEMS_HOME`` at a temporary folder so no test writes to the machine's root."""
    monkeypatch.setenv("SUSHISYSTEMS_HOME", str(tmp_path / "machine-root"))


@pytest.fixture(autouse=True)
def _clear_shared_style_cache():
    """Clear, after each test, the styles and colours Rich caches for one colour system."""
    yield
    _clear_caches(Style)
    _clear_caches(Color)


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
