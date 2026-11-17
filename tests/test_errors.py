# test_errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the errors a Sushi CLI reports to its user."""

import importlib
import inspect
import pkgutil
import types
from pathlib import Path

import pytest

import sushicore
from sushicore.errors import ConfigError, DigestMismatchError, SushiCoreError

pytestmark = pytest.mark.small


def test_a_config_error_is_a_sushicore_error_and_a_value_error():
    error = ConfigError("bad value")
    assert isinstance(error, SushiCoreError)
    assert isinstance(error, ValueError)


def test_a_digest_mismatch_names_the_file_and_both_digests():
    error = DigestMismatchError(Path("tool.zip"), expected="aa", actual="bb")
    assert (error.path, error.expected, error.actual) == (Path("tool.zip"), "aa", "bb")
    assert "tool.zip" in str(error)
    assert "bb" in str(error) and "pins aa" in str(error)


def _package_modules() -> list[types.ModuleType]:
    """Imports every module of the package except the runnable `__main__` ones."""
    names = [
        info.name
        for info in pkgutil.walk_packages(sushicore.__path__, "sushicore.")
        if not info.name.endswith(".__main__")
    ]
    return [importlib.import_module(name) for name in names]


def test_every_exception_the_package_defines_derives_from_sushicore_error():
    stray = [
        f"{module.__name__}.{name}"
        for module in _package_modules()
        for name, value in vars(module).items()
        if inspect.isclass(value)
        and value.__module__ == module.__name__
        and issubclass(value, BaseException)
        and not issubclass(value, SushiCoreError)
    ]
    assert stray == []
