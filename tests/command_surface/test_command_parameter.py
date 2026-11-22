# test_command_parameter.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a CLI keeping its own command declares a shared parameter in a plain Typer function."""

import pytest
import typer
from typer.testing import CliRunner

from sushicore.command_surface import BuildTypes, type_option

pytestmark = pytest.mark.small


def test_a_shared_parameter_declares_an_option_of_a_clis_own_command():
    parameter = type_option(BuildTypes(("debug", "release"), "debug"))
    seen = []
    app = typer.Typer()

    @app.command()
    def build(build_type: parameter.annotation = parameter.default) -> None:
        """Build."""
        seen.append(build_type.value)

    CliRunner().invoke(app, ["-t", "release"])
    assert seen == ["release"]
