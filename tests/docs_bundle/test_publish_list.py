# test_publish_list.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that `docs/publish.toml` is read, defaulted and refused the way the contract says."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.docs_bundle.errors import PublishListError
from sushicore.docs_bundle.publish_list import PublishList, read_publish_list
from sushicore.errors import ConfigError
from sushicore.files_memory import MemoryFiles

from .sample_repository import K_MEMORY_ROOT, write_file

K_MINIMAL = 'name = "sample"\ntitle = "Sample"\nsummary = "S."\nsections = ["guides"]\n'
K_DOCS = Path("docs")


def _read(text: str) -> PublishList:
    """Reads a publish list whose file holds *text*, held in memory."""
    return read_publish_list(K_DOCS, files=MemoryFiles({K_DOCS / "publish.toml": text}))


@pytest.mark.small
def test_read_returns_every_field(memory_repository):
    """Reads the sample file, orders the sections and trims the address."""
    assert read_publish_list(K_MEMORY_ROOT / "docs", files=memory_repository) == PublishList(
        name="sample",
        title="Sample",
        summary="A sample repository.",
        sections=("guides", "architecture"),
        exclude=frozenset(),
        api=False,
        source_url="https://github.com/SushiSystems/Sample",
    )


@pytest.mark.small
@pytest.mark.parametrize(
    ("extra", "exclude", "api"),
    [
        ("", frozenset(), False),
        ('exclude = ["guides/FAQ.md"]\napi = true\n', frozenset({"guides/FAQ.md"}), True),
    ],
)
def test_read_takes_exclude_and_api_as_written_or_by_default(extra, exclude, api):
    """Reads the exclusions as a set and the api flag as written; off and empty when omitted."""
    publish_list = _read(K_MINIMAL + extra)
    assert (publish_list.exclude, publish_list.api) == (exclude, api)


@pytest.mark.small
def test_read_leaves_the_address_unset_when_the_file_omits_it():
    """Gives no source address when the file has none."""
    assert _read(K_MINIMAL).source_url is None


@pytest.mark.small
def test_read_reports_a_missing_file():
    """Names the path when a repository has no publish list."""
    with pytest.raises(PublishListError) as caught:
        read_publish_list(K_DOCS, files=MemoryFiles())
    assert str(caught.value).startswith(f"{K_DOCS / 'publish.toml'} does not exist")


@pytest.mark.small
@pytest.mark.parametrize("section", ["design", "agent", "archive", "Guides"])
def test_read_refuses_a_section_that_cannot_be_published(section):
    """Refuses every section outside the four manual folders."""
    with pytest.raises(PublishListError) as caught:
        _read(K_MINIMAL.replace('"guides"', f'"{section}"'))
    assert f"section {section!r} cannot be published" in str(caught.value)


@pytest.mark.small
@pytest.mark.parametrize(
    ("text", "complaint"),
    [
        (K_MINIMAL.replace('name = "sample"\n', ""), "name must be a string that is not empty"),
        (K_MINIMAL.replace('"sample"', '"Sample Repo"'), "name must be lower-case letters"),
        (K_MINIMAL.replace('"S."', '""'), "summary must be a string that is not empty"),
        (K_MINIMAL.replace('["guides"]', "[]"), "sections must name at least one section"),
        (K_MINIMAL.replace('["guides"]', '"guides"'), "sections must be a list of strings"),
        (K_MINIMAL + 'api = "yes"\n', "api must be true or false"),
        (K_MINIMAL + "exclude = [1]\n", "exclude must be a list of strings"),
        (K_MINIMAL + 'source_url = "http://example.org"\n', "source_url must start with https://"),
        (K_MINIMAL + 'sectons = ["guides"]\n', "unknown key 'sectons'"),
    ],
)
def test_read_refuses_a_wrong_value_and_names_the_key(text, complaint):
    """Refuses a missing name, a bad name, an empty text, a wrong type and an unknown key."""
    with pytest.raises(PublishListError) as caught:
        _read(text)
    assert complaint in str(caught.value)


@pytest.mark.medium
def test_read_reports_malformed_toml_as_a_config_error(repository):
    """Leaves a file that is not TOML to the shared reader's own error."""
    write_file(repository, "docs/publish.toml", "name = ")
    with pytest.raises(ConfigError):
        read_publish_list(repository / "docs")
