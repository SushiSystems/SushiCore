# test_publish_list.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the reader of `docs/publish.toml` and every rule it enforces."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.docs_bundle.errors import PublishListError
from sushicore.docs_bundle.publish_list import PublishList, read_publish_list
from sushicore.errors import ConfigError

from .sample_repository import write_file

K_MINIMAL = 'name = "sample"\ntitle = "Sample"\nsummary = "S."\nsections = ["guides"]\n'


def _read(repository: Path, text: str) -> PublishList:
    """Replaces the sample's publish list with *text* and reads it."""
    write_file(repository, "docs/publish.toml", text)
    return read_publish_list(repository / "docs")


def test_read_returns_every_field(repository):
    """Reads the sample file, orders the sections and trims the address."""
    assert read_publish_list(repository / "docs") == PublishList(
        name="sample",
        title="Sample",
        summary="A sample repository.",
        sections=("guides", "architecture"),
        exclude=frozenset(),
        api=False,
        source_url="https://github.com/SushiSystems/Sample",
    )


def test_read_applies_the_defaults(repository):
    """Leaves exclude empty, api off and the address unset when the file omits them."""
    publish_list = _read(repository, K_MINIMAL)
    assert publish_list.exclude == frozenset()
    assert publish_list.api is False
    assert publish_list.source_url is None


def test_read_takes_exclude_and_api(repository):
    """Reads the exclusions as a set and the api flag as written."""
    publish_list = _read(repository, K_MINIMAL + 'exclude = ["guides/FAQ.md"]\napi = true\n')
    assert publish_list.exclude == frozenset({"guides/FAQ.md"})
    assert publish_list.api is True


def test_read_reports_a_missing_file(tmp_path):
    """Names the path when a repository has no publish list."""
    with pytest.raises(PublishListError) as caught:
        read_publish_list(tmp_path / "docs")
    assert "publish.toml" in str(caught.value)


@pytest.mark.parametrize("section", ["design", "agent", "archive", "Guides"])
def test_read_refuses_a_section_that_cannot_be_published(repository, section):
    """Refuses every section outside the four manual folders."""
    with pytest.raises(PublishListError) as caught:
        _read(repository, K_MINIMAL.replace('"guides"', f'"{section}"'))
    assert section in str(caught.value)


@pytest.mark.parametrize(
    "text",
    [
        K_MINIMAL.replace('name = "sample"\n', ""),
        K_MINIMAL.replace('"sample"', '"Sample Repo"'),
        K_MINIMAL.replace('"S."', '""'),
        K_MINIMAL.replace('["guides"]', "[]"),
        K_MINIMAL.replace('["guides"]', '"guides"'),
        K_MINIMAL + 'api = "yes"\n',
        K_MINIMAL + 'exclude = [1]\n',
        K_MINIMAL + 'source_url = "http://example.org"\n',
        K_MINIMAL + 'sectons = ["guides"]\n',
    ],
)
def test_read_refuses_a_wrong_value(repository, text):
    """Refuses a missing name, a bad name, an empty text, a wrong type and an unknown key."""
    with pytest.raises(PublishListError):
        _read(repository, text)


def test_read_reports_malformed_toml_as_a_config_error(repository):
    """Leaves a file that is not TOML to the shared reader's own error."""
    with pytest.raises(ConfigError):
        _read(repository, "name = ")
