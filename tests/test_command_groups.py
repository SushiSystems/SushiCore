# test_command_groups.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The groups a CLI adds beside its own commands are named once and checked in one place."""

import pytest
import typer

from sushicore.backlog import register_backlog_commands
from sushicore.command_groups import K_BACKLOG, K_DESIGN, K_GROUPS, exposed_groups, missing_groups
from sushicore.design import register_design_commands


pytestmark = pytest.mark.medium


def _app():
    app = typer.Typer()

    @app.callback()
    def root() -> None:
        """Root."""

    @app.command()
    def build() -> None:
        """Build."""

    return app


def test_the_groups_are_backlog_then_design():
    assert K_GROUPS == (K_BACKLOG, K_DESIGN) == ("backlog", "design")


def test_an_app_with_neither_group_lacks_both():
    assert missing_groups(_app()) == ["backlog", "design"]


def test_an_app_that_registered_a_group_through_sushicore_exposes_it(tmp_path):
    app = _app()
    register_backlog_commands(app, program="st", panel="Docs", project_root=lambda: tmp_path)
    register_design_commands(app, program="st", panel="Docs", project_root=lambda: tmp_path)
    assert missing_groups(app) == []
    assert {"backlog", "design", "build"} <= exposed_groups(app)


def test_a_caller_can_ask_for_another_set_of_names():
    assert missing_groups(_app(), ["build", "deploy"]) == ["deploy"]


def test_an_app_with_one_command_and_no_callback_exposes_nothing():
    app = typer.Typer()

    @app.command()
    def build() -> None:
        """Build."""

    assert exposed_groups(app) == frozenset()
    assert missing_groups(app) == ["backlog", "design"]
