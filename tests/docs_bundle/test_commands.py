# test_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the `docs` group a CLI registers: the bare form, `bundle`, and what it reports."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Callable

import typer
from typer.testing import CliRunner

import pytest

from sushicore.describe import catalogue
from sushicore.docs_bundle import ApiSource, PublishListError, register_docs_commands
from sushicore.docs_bundle.api_reference import RecordingApiBuild
from sushicore.docs_bundle.producer import BundleProducer
from sushicore.docs_bundle.source_revision import FixedCommit
from sushicore.files_memory import MemoryFiles

K_ROOT = Path("repo")
K_RELEASE_ARGUMENTS = ["docs", "bundle", "--release", "1.2.3"]


def _app(
    project_root: Path,
    reported: list[str],
    api: Callable[[], ApiSource] | None = None,
    producer: BundleProducer | None = None,
) -> typer.Typer:
    """Returns an application named `sx` with one command and the docs group."""
    app = typer.Typer(name="sx", no_args_is_help=True, add_completion=False)

    @app.command("build")
    def build() -> None:
        """Build."""

    register_docs_commands(
        app, program="sx", panel="Project", project_root=lambda: project_root,
        api=api, report=reported.append, producer=producer,
    )
    return app


def _source(build: RecordingApiBuild) -> ApiSource:
    """Returns an API source built by *build*."""
    return ApiSource(build=build, xml_dir=K_ROOT / "xml")


def _producer() -> BundleProducer:
    """Returns a producer that records a fixed commit, so no git runs."""
    return BundleProducer(read_commit=FixedCommit("c0ffee"))


@pytest.mark.small
def test_bare_docs_builds_the_api_and_returns_its_code():
    """`sx docs` runs the API build once and exits with what it returns."""
    build = RecordingApiBuild(code=4)
    source = _source(build)
    result = CliRunner().invoke(_app(K_ROOT, [], api=lambda: source), ["docs"])
    assert (result.exit_code, build.calls) == (4, 1)


@pytest.mark.small
def test_the_group_works_where_click_is_not_installed(monkeypatch):
    """Registers and runs with Typer alone, as a Typer that carries its own Click requires."""
    monkeypatch.setitem(sys.modules, "click", None)
    source = _source(RecordingApiBuild(code=4))
    result = CliRunner().invoke(_app(K_ROOT, [], api=lambda: source), ["docs"])
    assert result.exit_code == 4


@pytest.mark.small
def test_bare_docs_shows_help_when_the_cli_builds_no_api():
    """`sx docs` lists `bundle` when there is no API reference to build."""
    result = CliRunner().invoke(_app(K_ROOT, []), ["docs"])
    assert "bundle" in result.output


@pytest.mark.medium
def test_bundle_writes_the_archive_under_the_default_folder(repository):
    """`sx docs bundle --release` writes under build/docs/bundle."""
    result = CliRunner().invoke(
        _app(repository, [], producer=_producer()), K_RELEASE_ARGUMENTS)
    assert result.exit_code == 0, result.output
    assert (repository / "build" / "docs" / "bundle" / "docs-bundle-1.2.3.tar.gz").is_file()


@pytest.mark.medium
def test_bundle_reports_the_archive_and_its_digest(repository):
    """Reports the archive with its page count, then the SHA-256 of the archive."""
    reported: list[str] = []
    CliRunner().invoke(_app(repository, reported, producer=_producer()), K_RELEASE_ARGUMENTS)
    archive = repository / "build" / "docs" / "bundle" / "docs-bundle-1.2.3.tar.gz"
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert reported == [f"{archive} (3 pages)", f"sha256 {digest}"]


@pytest.mark.medium
def test_bundle_writes_where_out_says(checkout, tmp_path):
    """`--out` moves the archive."""
    arguments = ["docs", "bundle", "--release", "1.2.3", "--out", str(tmp_path / "elsewhere")]
    assert CliRunner().invoke(_app(checkout, []), arguments).exit_code == 0
    assert (tmp_path / "elsewhere" / "docs-bundle-1.2.3.tar.gz").is_file()


@pytest.mark.small
def test_bundle_requires_a_release():
    """`sx docs bundle` without `--release` is a usage error."""
    assert CliRunner().invoke(_app(K_ROOT, []), ["docs", "bundle"]).exit_code == 2


@pytest.mark.small
def test_bundle_lets_a_bundle_error_reach_the_entry_point():
    """A missing publish list leaves the command as the error `entry.run` prints."""
    producer = BundleProducer(read_commit=FixedCommit("c0ffee"), files=MemoryFiles())
    result = CliRunner().invoke(_app(K_ROOT, [], producer=producer), K_RELEASE_ARGUMENTS)
    assert isinstance(result.exception, PublishListError)


@pytest.mark.small
def test_the_catalogue_holds_docs_only_when_it_runs_bare():
    """`--describe` lists `docs` for a CLI with an API and `docs bundle` for every CLI."""
    source = _source(RecordingApiBuild())
    with_api = catalogue(_app(K_ROOT, [], api=lambda: source), distribution="sushicore")
    without = catalogue(_app(K_ROOT, []), distribution="sushicore")
    assert [c["name"] for c in with_api["commands"]] == ["build", "docs", "docs bundle"]
    assert [c["name"] for c in without["commands"]] == ["build", "docs bundle"]
