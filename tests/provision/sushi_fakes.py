# sushi_fakes.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""A fake git and fragment writers shared by the tests of pinned Sushi libraries."""

from __future__ import annotations

from pathlib import Path

from sushicore.provision.git_client import IGitClient

#: The commit the fixtures pin.
K_PINNED = "0123456789abcdef0123456789abcdef01234567"

#: A commit that is not the pin.
K_OTHER = "fedcba9876543210fedcba9876543210fedcba98"


class FakeGit(IGitClient):
    """Records clones; a clone creates the folder and leaves HEAD at *commit*."""

    def __init__(self, commit: str = K_PINNED, clones: bool = True,
                 heads: dict[Path, str] | None = None) -> None:
        """Hold the commit a clone lands on, whether clones succeed, and fixed HEADs."""
        self.commit = commit
        self.clones = clones
        self.heads = {path.resolve(): head for path, head in (heads or {}).items()}
        self.calls: list[tuple[str, str, Path]] = []

    def clone_tag(self, url: str, tag: str, destination: Path, dry_run: bool) -> bool:
        """Record the clone and create *destination* when clones succeed."""
        self.calls.append((url, tag, destination))
        if not self.clones:
            return False
        destination.mkdir(parents=True)
        self.heads[destination.resolve()] = self.commit
        return True

    def head(self, checkout: Path) -> str:
        """Return the HEAD recorded for *checkout*, else ''."""
        return self.heads.get(checkout.resolve(), "")


def write_fragment(checkout: Path, pins: dict[str, str]) -> Path:
    """Write *checkout*'s fragment pinning each name of *pins* at its version to K_PINNED."""
    path = checkout / "cli" / "sushistack.deps.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    names = ", ".join(f'"{name}"' for name in pins)
    tables = "".join(f'[sushisystems.{name}]\nversion = "{version}"\ncommit = "{K_PINNED}"\n'
                     for name, version in pins.items())
    path.write_text(f"[module]\ndepends_on = [{names}]\n{tables}", encoding="utf-8")
    return path
