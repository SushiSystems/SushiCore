# publish_list.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reads `docs/publish.toml`, the list of what a repository publishes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..workspace import read_toml
from .errors import PublishListError

K_FILE_NAME = "publish.toml"
K_SECTIONS: tuple[str, ...] = ("getting_started", "guides", "architecture", "reference")
K_KEYS = frozenset({"name", "title", "summary", "sections", "exclude", "api", "source_url"})
K_NAME = re.compile(r"^[a-z][a-z0-9]*$")
K_ADDRESS_PREFIX = "https://"


@dataclass(frozen=True, slots=True)
class PublishList:
    """Holds what one repository publishes and how the site names it."""

    name: str
    title: str
    summary: str
    sections: tuple[str, ...]
    exclude: frozenset[str]
    api: bool
    source_url: str | None


def _text(path: Path, document: dict, key: str) -> str:
    """Returns a required key's value, which must be a string that is not empty."""
    value = document.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PublishListError(f"{path}: {key} must be a string that is not empty.")
    return value.strip()


def _names(path: Path, document: dict, key: str) -> tuple[str, ...]:
    """Returns an optional key's value, which must be a list of strings."""
    value = document.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PublishListError(f"{path}: {key} must be a list of strings.")
    return tuple(value)


def _sections(path: Path, document: dict) -> tuple[str, ...]:
    """Returns the published sections in manual order, refusing any other folder."""
    listed = _names(path, document, "sections")
    if not listed:
        raise PublishListError(f"{path}: sections must name at least one section.")
    for section in listed:
        if section not in K_SECTIONS:
            raise PublishListError(
                f"{path}: section {section!r} cannot be published; "
                f"the sections are {', '.join(K_SECTIONS)}."
            )
    return tuple(section for section in K_SECTIONS if section in listed)


def _source_url(path: Path, document: dict) -> str | None:
    """Returns the repository's address without a trailing slash, or None when unset."""
    if "source_url" not in document:
        return None
    value = _text(path, document, "source_url")
    if not value.startswith(K_ADDRESS_PREFIX):
        raise PublishListError(f"{path}: source_url must start with {K_ADDRESS_PREFIX}.")
    return value.rstrip("/")


def read_publish_list(docs_dir: Path) -> PublishList:
    """Reads and validates the publish list of the documentation tree at *docs_dir*.

    Raises:
        PublishListError: The file is missing, or a key is unknown or holds a wrong value.
    """
    path = docs_dir / K_FILE_NAME
    if not path.is_file():
        raise PublishListError(
            f"{path} does not exist; a repository lists what it publishes there."
        )
    document = read_toml(path)
    unknown = sorted(set(document) - K_KEYS)
    if unknown:
        raise PublishListError(
            f"{path}: unknown key {unknown[0]!r}; the keys are {', '.join(sorted(K_KEYS))}."
        )
    name = _text(path, document, "name")
    if not K_NAME.match(name):
        raise PublishListError(f"{path}: name must be lower-case letters and digits.")
    api = document.get("api", False)
    if not isinstance(api, bool):
        raise PublishListError(f"{path}: api must be true or false.")
    return PublishList(
        name=name,
        title=_text(path, document, "title"),
        summary=_text(path, document, "summary"),
        sections=_sections(path, document),
        exclude=frozenset(_names(path, document, "exclude")),
        api=api,
        source_url=_source_url(path, document),
    )
