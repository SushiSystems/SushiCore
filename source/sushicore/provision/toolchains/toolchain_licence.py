# toolchain_licence.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Installs the licence texts of the llvm-sycl toolchain beside its libraries."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from ...errors import SushiCoreError

__all__ = [
    "LICENCE_FILE", "LICENCE_MARKER", "LICENCE_SUBDIR", "LicenceTextError",
    "bundled_licence", "fetch_licence", "install_licence", "licence_path", "llvm_licence_url"]

#: The folder under the toolchain root that holds one folder of licence text per component.
LICENCE_SUBDIR = Path("share") / "licenses" / "llvm-sycl"

#: The file name every component's licence text is installed under.
LICENCE_FILE = "LICENSE.TXT"

#: The clause that marks a text as Apache-2.0 with the LLVM exception, which all three components carry.
LICENCE_MARKER = "LLVM Exceptions"

_LLVM_RAW_URL = "https://raw.githubusercontent.com/intel/llvm/{ref}/llvm/LICENSE.TXT"


class LicenceTextError(SushiCoreError, RuntimeError):
    """A component's licence text is missing or is not the Apache-2.0 with LLVM exception text."""


def licence_path(root: Path, component: str) -> Path:
    """Return where *component*'s licence text lives under the toolchain *root*."""
    return root / LICENCE_SUBDIR / component / LICENCE_FILE


def llvm_licence_url(ref: str) -> str:
    """Return the raw GitHub URL of LLVM's ``LICENSE.TXT`` in intel/llvm at the tag or commit *ref*."""
    return _LLVM_RAW_URL.format(ref=ref)


def bundled_licence(root: Path) -> Path | None:
    """Return the ``LICENSE.TXT`` the extracted bundle carries at its root, or None."""
    candidate = root / LICENCE_FILE
    return candidate if candidate.is_file() else None


def install_licence(root: Path, component: str, source: Path) -> Path:
    """Copy the text at *source* to *component*'s place under *root* and return that place.

    Args:
        root: The toolchain root.
        component: The component the text belongs to, such as ``llvm``.
        source: The file holding the text.

    Raises:
        LicenceTextError: *source* is missing, unreadable, empty or lacks the LLVM exception clause.
    """
    try:
        text = source.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise LicenceTextError(f"the {component} licence text cannot be read at {source}: {exc}") from exc
    if not text.strip():
        raise LicenceTextError(f"the {component} licence text at {source} is empty")
    if LICENCE_MARKER not in text:
        raise LicenceTextError(
            f"the {component} licence text at {source} does not carry the "
            f"'{LICENCE_MARKER}' clause of Apache-2.0 with the LLVM exception")
    destination = licence_path(root, component)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return destination


def fetch_licence(root: Path, component: str, url: str, scratch: Path,
                  fetch: Callable[[str, Path], None]) -> Path:
    """Download *url* into *scratch* with *fetch* and install it as *component*'s text.

    Raises:
        LicenceTextError: The download fails or the text is not the expected licence.
    """
    try:
        fetch(url, scratch)
    except Exception as exc:
        raise LicenceTextError(f"the {component} licence text cannot be fetched from {url}: {exc}") from exc
    return install_licence(root, component, scratch)
