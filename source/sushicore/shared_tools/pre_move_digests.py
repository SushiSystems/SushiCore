# pre_move_digests.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Knows the digests of the shared files as SushiSkills held them before the move to SushiCore."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path

from ..errors import ConfigError
from ..layered_toml import read_toml
from .errors import SharedToolsError

K_DIGESTS_PATH = Path(__file__).with_name("pre_move_digests.toml")
K_FORMAT_VERSION = 1
PreMoveDigests = Mapping[str, frozenset[str]]


def body_digest(body: str) -> str:
    """Returns the SHA-256 of a file body, as UTF-8 bytes, in hex."""
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def is_pre_move_copy(digests: PreMoveDigests, path: str, body: str) -> bool:
    """Returns whether a body is one SushiSkills held for the path before the move."""
    return body_digest(body) in digests.get(path, frozenset())


def read_pre_move_digests(source: Path = K_DIGESTS_PATH) -> dict[str, frozenset[str]]:
    """Returns the digests of each path from the frozen data file.

    Raises:
        SharedToolsError: The file is unreadable or is not a version this reader knows.
    """
    try:
        data = read_toml(source)
        version = data["format_version"]
        if version != K_FORMAT_VERSION:
            raise SharedToolsError(
                f"{source} is format version {version}, this reader knows {K_FORMAT_VERSION}"
            )
        return {path: frozenset(row["digests"]) for path, row in data.get("files", {}).items()}
    except (ConfigError, KeyError, TypeError) as error:
        raise SharedToolsError(f"{source} is not a pre-move digest file: {error}") from error
