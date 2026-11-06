# sushi_fakes.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The pinned commits and the fragment writer shared by the tests of pinned Sushi libraries."""

from __future__ import annotations

from pathlib import Path

from sushicore.provision.git_client_memory import InMemoryGitClient

#: The commit the fixtures pin.
K_PINNED = "0123456789abcdef0123456789abcdef01234567"

#: A commit that is not the pin.
K_OTHER = "fedcba9876543210fedcba9876543210fedcba98"


def _make_folder(destination: Path) -> None:
    """Create the folder a clone lands in, as a real clone does."""
    destination.mkdir(parents=True)


def pinned_git(commit: str = K_PINNED, **changes) -> InMemoryGitClient:
    """Return an in-memory git whose clones land on *commit* and leave a folder on disk."""
    return InMemoryGitClient(commit=commit, materialize=_make_folder, **changes)


def write_fragment(checkout: Path, pins: dict[str, str]) -> Path:
    """Write *checkout*'s fragment pinning each name of *pins* at its version to K_PINNED."""
    path = checkout / "cli" / "sushistack.deps.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    names = ", ".join(f'"{name}"' for name in pins)
    tables = "".join(f'[sushisystems.{name}]\nversion = "{version}"\ncommit = "{K_PINNED}"\n'
                     for name, version in pins.items())
    path.write_text(f"[module]\ndepends_on = [{names}]\n{tables}", encoding="utf-8")
    return path
