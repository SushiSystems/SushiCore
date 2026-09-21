"""Shared fixtures for the whole suite."""

import pytest
from rich.color import Color
from rich.style import Style


def _clear_caches(owner: type) -> None:
    """Clear every functools cache on ``owner``."""
    for name in dir(owner):
        clear = getattr(getattr(owner, name, None), "cache_clear", None)
        if clear is not None:
            clear()


@pytest.fixture(autouse=True)
def _clear_shared_style_cache():
    """Clear, after each test, the styles and colours Rich caches for one colour system."""
    yield
    _clear_caches(Style)
    _clear_caches(Color)
