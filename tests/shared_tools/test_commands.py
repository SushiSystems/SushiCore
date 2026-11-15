# test_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the `sync` and `check` commands as a CLI registers them."""

from __future__ import annotations

import pytest
import typer
from typer.testing import CliRunner

from sushicore.shared_tools import register_shared_tools_commands

from .conftest import K_SHARED, K_TAG

pytestmark = pytest.mark.medium


@pytest.fixture()
def app() -> typer.Typer:
    """Returns an application that carries the two commands."""
    application = typer.Typer()
    register_shared_tools_commands(application, program="tool")
    return application


def test_sync_reports_each_file_it_writes(app, upstream, target):
    """The report names a file and says it was written."""
    result = CliRunner().invoke(app, ["sync", str(target), "--tag", K_TAG, "--from", str(upstream)])
    assert result.exit_code == 0
    assert f"{K_SHARED}: written" in result.output


def test_dry_run_reports_what_it_would_write(app, upstream, target):
    """A dry run says would write and leaves the repository as it was."""
    result = CliRunner().invoke(app, ["sync", str(target), "--tag", K_TAG, "--from", str(upstream), "--dry-run"])
    assert f"{K_SHARED}: would write" in result.output
    assert not (target / K_SHARED).exists()


def test_sync_of_a_missing_root_exits_2(app, tmp_path):
    """A root that is not a directory is a request that cannot be acted on."""
    result = CliRunner().invoke(app, ["sync", str(tmp_path / "none"), "--tag", K_TAG])
    assert result.exit_code == 2
