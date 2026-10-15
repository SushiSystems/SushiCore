# conftest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Shared fixtures for the whole suite, and the size rules every test follows."""

import faulthandler

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


K_SIZE_TIMEOUTS = {"small": 60, "medium": 300, "large": 900}


def _sizes_of(item: pytest.Item) -> list[str]:
    """Return the size labels *item* carries, one entry per label."""
    return [mark.name for mark in item.iter_markers() if mark.name in K_SIZE_TIMEOUTS]


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Fail collection when a test carries no size or more than one."""
    wrong = [f"{item.nodeid}: {_sizes_of(item) or 'no size'}"
             for item in items if len(_sizes_of(item)) != 1]
    if wrong:
        listing = ", ".join(wrong)
        raise pytest.UsageError(f"every test carries exactly one size: {listing}")


@pytest.hookimpl(wrapper=True)
def pytest_runtest_protocol(item: pytest.Item, nextitem: pytest.Item | None):
    """Stop the run with a traceback dump when a test outlives the timeout of its size."""
    sizes = _sizes_of(item)
    if len(sizes) == 1:
        faulthandler.dump_traceback_later(K_SIZE_TIMEOUTS[sizes[0]], exit=True)
    try:
        return (yield)
    finally:
        faulthandler.cancel_dump_traceback_later()
