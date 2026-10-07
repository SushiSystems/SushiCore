# test_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the `docs` group a CLI registers: the bare form, `bundle`, and what it reports."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import typer
from typer.testing import CliRunner

from sushicore.describe import catalogue
from sushicore.docs_bundle import ApiSource, PublishListError, register_docs_commands


def _app(
    repository: Path, reported: list[str], api: Callable[[], ApiSource] | None = None,
) -> typer.Typer:
    """Returns an application named `sx` with one command and the docs group."""
    app = typer.Typer(name="sx", no_args_is_help=True, add_completion=False)

    @app.command("build")
    def build() -> None:
        """Build."""

    register_docs_commands(
        app, program="sx", panel="Project", project_root=lambda: repository,
        api=api, report=reported.append,
    )
    return app


def test_bare_docs_builds_the_api_and_returns_its_code(repository):
    """`sx docs` runs the API build and exits with what it returns."""
    calls: list[str] = []
    source = ApiSource(build=lambda: calls.append("build") or 4, xml_dir=repository / "xml")
    result = CliRunner().invoke(_app(repository, [], api=lambda: source), ["docs"])
    assert result.exit_code == 4
    assert calls == ["build"]


def test_bare_docs_shows_help_when_the_cli_builds_no_api(repository):
    """`sx docs` lists `bundle` when there is no API reference to build."""
    result = CliRunner().invoke(_app(repository, []), ["docs"])
    assert "bundle" in result.output


def test_bundle_writes_the_archive_and_reports_it(checkout):
    """`sx docs bundle --release` writes under build/docs/bundle and reports two lines."""
    reported: list[str] = []
    result = CliRunner().invoke(_app(checkout, reported), ["docs", "bundle", "--release", "1.2.3"])
    assert result.exit_code == 0, result.output
    archive = checkout / "build" / "docs" / "bundle" / "docs-bundle-1.2.3.tar.gz"
    assert archive.is_file()
    assert reported[0] == f"{archive} (3 pages)"
    assert reported[1].startswith("sha256 ") and len(reported[1]) == 7 + 64


def test_bundle_writes_where_out_says(checkout, tmp_path):
    """`--out` moves the archive."""
    arguments = ["docs", "bundle", "--release", "1.2.3", "--out", str(tmp_path / "elsewhere")]
    assert CliRunner().invoke(_app(checkout, []), arguments).exit_code == 0
    assert (tmp_path / "elsewhere" / "docs-bundle-1.2.3.tar.gz").is_file()


def test_bundle_requires_a_release(repository):
    """`sx docs bundle` without `--release` is a usage error."""
    assert CliRunner().invoke(_app(repository, []), ["docs", "bundle"]).exit_code == 2


def test_bundle_lets_a_bundle_error_reach_the_entry_point(repository):
    """A broken publish list leaves the command as the error `entry.run` prints."""
    (repository / "docs" / "publish.toml").unlink()
    result = CliRunner().invoke(_app(repository, []), ["docs", "bundle", "--release", "1.2.3"])
    assert isinstance(result.exception, PublishListError)


def test_the_catalogue_holds_docs_only_when_it_runs_bare(repository):
    """`--describe` lists `docs` for a CLI with an API and `docs bundle` for every CLI."""
    source = ApiSource(build=lambda: 0, xml_dir=repository / "xml")
    with_api = catalogue(_app(repository, [], api=lambda: source), distribution="sushicore")
    without = catalogue(_app(repository, []), distribution="sushicore")
    assert [c["name"] for c in with_api["commands"]] == ["build", "docs", "docs bundle"]
    assert [c["name"] for c in without["commands"]] == ["build", "docs bundle"]
