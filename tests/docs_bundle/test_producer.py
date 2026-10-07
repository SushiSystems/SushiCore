# test_producer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the producer end to end on the sample repository."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

import pytest

from sushicore.docs_bundle.api_reference import ApiSource
from sushicore.docs_bundle.errors import ApiReferenceError, ReleaseError
from sushicore.docs_bundle.producer import BundleProducer, BundleRequest, BundleResult
from sushicore.docs_bundle.source_revision import read_head_commit

from .sample_repository import K_PUBLISH, commit_all, write_file

K_COMMIT = "c0ffee"


def _produce(
    repository: Path, out: Path, release: str = "1.2.3", api: ApiSource | None = None,
) -> BundleResult:
    """Produces the sample's bundle into *out* with a fixed commit."""
    producer = BundleProducer(read_commit=lambda root: K_COMMIT)
    return producer.produce(BundleRequest(repository, release, out, api))


def _names(archive: Path) -> list[str]:
    """Returns the member names of an archive."""
    with tarfile.open(archive, "r:gz") as packed:
        return packed.getnames()


def _manifest(archive: Path) -> dict:
    """Returns the bundle.json an archive carries."""
    with tarfile.open(archive, "r:gz") as packed:
        return json.loads(packed.extractfile("bundle.json").read().decode("utf-8"))


def test_produce_writes_the_pages_the_assets_and_the_manifest(repository, tmp_path):
    """Packs the published pages, their asset and bundle.json, and nothing unpublished."""
    result = _produce(repository, tmp_path / "out")
    assert result.archive == tmp_path / "out" / "docs-bundle-1.2.3.tar.gz"
    assert result.page_count == 3
    assert _names(result.archive) == [
        "bundle.json",
        "pages/architecture/OVERVIEW.md",
        "pages/guides/BUILDING.md",
        "pages/guides/FAQ.md",
        "pages/guides/images/shot.png",
    ]
    manifest = _manifest(result.archive)
    assert (manifest["version"], manifest["commit"], manifest["api"]) == ("1.2.3", K_COMMIT, None)


def test_produce_is_reproducible_and_replaces_an_earlier_staging(repository, tmp_path):
    """Gives the same digest twice, and a file left in staging does not reach the archive."""
    first = _produce(repository, tmp_path / "out")
    write_file(tmp_path / "out", ".docs-bundle-staging/pages/guides/LEFTOVER.md", "# Old\n")
    second = _produce(repository, tmp_path / "out")
    assert first.sha256 == second.sha256
    assert "pages/guides/LEFTOVER.md" not in _names(second.archive)


@pytest.mark.parametrize("release", ["v1.2.3", "1.2", "1.2.3-rc1", ""])
def test_produce_refuses_a_release_that_is_not_three_integers(repository, tmp_path, release):
    """Refuses a tag's v, a short version and a pre-release suffix."""
    with pytest.raises(ReleaseError):
        _produce(repository, tmp_path / "out", release=release)


def test_produce_carries_the_api_when_the_list_asks_for_it(repository, tmp_path):
    """Packs api/xml and names it in the manifest when publish.toml sets api = true."""
    write_file(repository, "docs/publish.toml", K_PUBLISH + "api = true\n")
    xml_dir = tmp_path / "xml"
    write_file(xml_dir, "index.xml", "<doxygenindex/>\n")
    result = _produce(repository, tmp_path / "out", api=ApiSource(lambda: 0, xml_dir))
    assert "api/xml/index.xml" in _names(result.archive)
    assert _manifest(result.archive)["api"] == {"format": "doxygen-xml", "root": "api/xml"}


def test_produce_stops_when_the_list_asks_for_an_api_nobody_builds(repository, tmp_path):
    """Fails before writing an archive when api = true and no source was given."""
    write_file(repository, "docs/publish.toml", K_PUBLISH + "api = true\n")
    with pytest.raises(ApiReferenceError):
        _produce(repository, tmp_path / "out")
    assert not (tmp_path / "out" / "docs-bundle-1.2.3.tar.gz").exists()


def test_read_head_commit_returns_the_checked_out_hash(repository):
    """Reads the full hash of HEAD from a real checkout."""
    committed = commit_all(repository)
    assert read_head_commit(repository) == committed


def test_read_head_commit_reports_a_folder_that_is_no_checkout(tmp_path, monkeypatch):
    """Reports a folder outside any repository as a release error."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    with pytest.raises(ReleaseError):
        read_head_commit(tmp_path)
