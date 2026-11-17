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
from sushicore.deps_fragment import read
from sushicore.events import UnknownEventKindError, event_line
from sushicore.errors import (
    ConfigError,
    DigestMismatchError,
    ProjectRootNotFoundError,
    SushiCoreError,
)
from sushicore.provision.links import NotADirectoryLinkError, remove_dir_link

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


#: Exceptions that carry control flow, not a failure, so they are not package errors.
K_CONTROL_FLOW_SIGNALS = frozenset({"sushicore.testing.session._Stop"})


def test_a_missing_project_root_is_a_sushicore_error_and_not_a_system_exit():
    assert issubclass(ProjectRootNotFoundError, SushiCoreError)
    assert not issubclass(ProjectRootNotFoundError, SystemExit)


def test_an_unknown_event_kind_is_a_sushicore_error_and_still_a_value_error():
    with pytest.raises(UnknownEventKindError) as raised:
        event_line("nonsense")
    assert isinstance(raised.value, (SushiCoreError, ValueError))


def test_a_malformed_fragment_raises_a_config_error(tmp_path):
    fragment = tmp_path / "sushistack.deps.toml"
    fragment.write_text("module = 3", encoding="utf-8")
    with pytest.raises(ConfigError):
        read(fragment)


def test_removing_a_plain_folder_as_a_link_raises_a_package_error(tmp_path):
    with pytest.raises(NotADirectoryLinkError):
        remove_dir_link(tmp_path)


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
    stray = [name for name in stray if name not in K_CONTROL_FLOW_SIGNALS]
    assert stray == []
