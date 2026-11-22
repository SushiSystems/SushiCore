# test_errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that every failure of the command surface reaches an entry point as one SushiCore error."""

import pytest

from sushicore.command_surface import (BuildTypeError, CommandSurfaceError, DomainPanelError,
                                       ParameterNameError, SanitizerConflictError, UnknownSanitizerError,
                                       UnknownVerbError)
from sushicore.errors import SushiCoreError

pytestmark = pytest.mark.small


@pytest.mark.parametrize("error", [
    BuildTypeError, DomainPanelError, ParameterNameError, SanitizerConflictError, UnknownSanitizerError,
    UnknownVerbError,
])
def test_each_command_surface_error_is_caught_as_its_module_base_and_as_a_sushicore_error(error):
    assert issubclass(error, CommandSurfaceError) and issubclass(error, SushiCoreError)
