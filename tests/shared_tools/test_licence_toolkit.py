# test_licence_toolkit.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the writer of a tag loads, and that loading it leaves the interpreter as it was."""

from __future__ import annotations

import sys

import pytest

from sushicore.shared_tools import GitReader
from sushicore.shared_tools.licence_toolkit import load_toolkit

from .conftest import K_TAG

pytestmark = pytest.mark.medium


def test_the_toolkit_loads_and_leaves_sys_path_and_modules_as_they_were(upstream):
    """Inside the block the writer works; after it neither sys.path nor sys.modules changed."""
    paths, modules = list(sys.path), set(sys.modules)
    with load_toolkit(GitReader(upstream), K_TAG) as toolkit:
        assert toolkit.is_source("a.py")
        assert not toolkit.is_source("a.md")
    assert sys.path == paths
    assert set(sys.modules) == modules
