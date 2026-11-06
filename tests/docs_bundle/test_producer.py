# test_producer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the producer stages, checks and packs a repository's documentation."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

import pytest

from sushicore.docs_bundle.api_reference import ApiSource, RecordingApiBuild
from sushicore.docs_bundle.errors import ApiReferenceError, ReleaseError
from sushicore.docs_bundle.producer import BundleProducer, BundleRequest, BundleResult
from sushicore.docs_bundle.source_revision import FixedCommit, read_head_commit

from .sample_repository import K_PUBLISH, commit_all, write_file


K_COMMIT = "c0ffee"


def _produce(
    repository: Path, out: Path, release: str = "1.2.3", api: ApiSource | None = None,
) -> BundleResult:
    """Produces the repository's bundle into *out* with a fixed commit."""
    producer = BundleProducer(read_commit=FixedCommit(K_COMMIT))
    return producer.produce(BundleRequest(repository, release, out, api))


def _names(archive: Path) -> list[str]:
    """Returns the member names of an archive."""
    with tarfile.open(archive, "r:gz") as packed:
        return packed.getnames()


def _manifest(archive: Path) -> dict:
    """Returns the bundle.json an archive carries."""
    with tarfile.open(archive, "r:gz") as packed:
        return json.loads(packed.extractfile("bundle.json").read().decode("utf-8"))


@pytest.fixture
def produced(repository, tmp_path) -> BundleResult:
    """Returns the result of producing the sample's bundle into a temporary folder."""
    return _produce(repository, tmp_path / "out")


@pytest.mark.medium
def test_produce_names_the_archive_after_the_release_and_counts_its_pages(produced, tmp_path):
    """Writes `docs-bundle-<release>.tar.gz` into the output folder and counts the pages."""
    assert produced.archive == tmp_path / "out" / "docs-bundle-1.2.3.tar.gz"
    assert produced.page_count == 3


@pytest.mark.medium
def test_produce_packs_the_published_pages_and_their_assets_and_nothing_unpublished(produced):
    """Packs bundle.json, the three pages and the image, not the design page or the root README."""
    assert _names(produced.archive) == [
        "bundle.json",
        "pages/architecture/OVERVIEW.md",
        "pages/guides/BUILDING.md",
        "pages/guides/FAQ.md",
        "pages/guides/images/shot.png",
    ]


@pytest.mark.medium
def test_produce_records_the_release_and_the_commit_in_the_manifest(produced):
    """Writes the release, the commit and no API into bundle.json."""
    manifest = _manifest(produced.archive)
    assert (manifest["version"], manifest["commit"], manifest["api"]) == ("1.2.3", K_COMMIT, None)


@pytest.mark.medium
def test_produce_gives_the_same_digest_twice(repository, tmp_path):
    """Gives the same digest when the same repository is produced into the same folder twice."""
    first = _produce(repository, tmp_path / "out")
    second = _produce(repository, tmp_path / "out")
    assert first.sha256 == second.sha256


@pytest.mark.medium
def test_produce_replaces_an_earlier_staging(repository, tmp_path):
    """Keeps a file left in the staging folder out of the archive."""
    _produce(repository, tmp_path / "out")
    write_file(tmp_path / "out", ".docs-bundle-staging/pages/guides/LEFTOVER.md", "# Old\n")
    second = _produce(repository, tmp_path / "out")
    assert "pages/guides/LEFTOVER.md" not in _names(second.archive)


@pytest.mark.small
@pytest.mark.parametrize("release", ["v1.2.3", "1.2", "1.2.3-rc1", "", "1.2.3\n"])
def test_produce_refuses_a_release_that_is_not_three_integers(release):
    """Refuses a tag's v, a short version and a pre-release suffix before it reads any file."""
    producer = BundleProducer(read_commit=FixedCommit(K_COMMIT))
    with pytest.raises(ReleaseError):
        producer.produce(BundleRequest(Path("repo"), release, Path("out")))


@pytest.mark.medium
def test_produce_carries_the_api_when_the_list_asks_for_it(repository, tmp_path):
    """Packs api/xml and names it in the manifest when publish.toml sets api = true."""
    write_file(repository, "docs/publish.toml", K_PUBLISH + "api = true\n")
    xml_dir = tmp_path / "xml"
    build = RecordingApiBuild(written={xml_dir / "index.xml": "<doxygenindex/>\n"})
    result = _produce(repository, tmp_path / "out", api=ApiSource(build, xml_dir))
    assert "api/xml/index.xml" in _names(result.archive)
    assert _manifest(result.archive)["api"] == {"format": "doxygen-xml", "root": "api/xml"}


@pytest.mark.medium
def test_produce_stops_when_the_list_asks_for_an_api_nobody_builds(repository, tmp_path):
    """Fails before writing an archive when api = true and no source was given."""
    write_file(repository, "docs/publish.toml", K_PUBLISH + "api = true\n")
    with pytest.raises(ApiReferenceError):
        _produce(repository, tmp_path / "out")
    assert not (tmp_path / "out" / "docs-bundle-1.2.3.tar.gz").exists()


@pytest.mark.medium
def test_read_head_commit_returns_the_checked_out_hash(repository):
    """Reads the full hash of HEAD from a real checkout."""
    committed = commit_all(repository)
    assert read_head_commit(repository) == committed
