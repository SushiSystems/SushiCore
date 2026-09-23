# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Provenance stamp recorded beside an installed SYCL toolchain tree.

Without it an install is a black box — the tree carries no version anywhere a
tool can read, so a stale bundle stays invisible until something it lacks
fails much further downstream.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .. import home

#: Records which release a toolchain tree came from, written beside the bundle.
TOOLCHAIN_STAMP = ".sushi_toolchain.json"


def toolchains_dir() -> Path:
    """Return the base directory for SYCL toolchains installed by provisioning."""
    return home.toolchains_dir()


def read_toolchain_stamp(root: Path) -> dict:
    """Return the recorded provenance of a toolchain tree, or an empty dict.

    :param root: Bundle root (the directory holding ``bin/`` and ``lib/``).
    :return: The stamp's fields (``source``, ``tag``, ``adapters``), empty when
        absent, unreadable, invalid JSON or not a JSON object.
    """
    try:
        data = json.loads((root / TOOLCHAIN_STAMP).read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _rewrite_stamp(root: Path, mutate) -> None:
    """Apply *mutate* to the stamp's current fields and write it back atomically.

    :param mutate: Called with the stamp dict; changes it in place.
    """
    stamp = read_toolchain_stamp(root)
    mutate(stamp)
    path = root / TOOLCHAIN_STAMP
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(json.dumps(stamp, indent=2))
        os.replace(tmp, path)
    except OSError:
        tmp.unlink(missing_ok=True)


def write_toolchain_stamp(root: Path, source: str, tag: str) -> None:
    """Record where a freshly installed toolchain tree came from.

    Preserves every other field already in the stamp, such as ``adapters``.
    """
    def mutate(stamp: dict) -> None:
        stamp["source"] = source
        stamp["tag"] = tag
    _rewrite_stamp(root, mutate)


def record_toolchain_adapter(root: Path, vendor: str, commit: str) -> None:
    """Record *vendor*'s adapter commit in the stamp, keeping its other fields.

    :param root: Bundle root (the directory holding ``bin/`` and ``lib/``).
    :param vendor: The backend's own vendor name.
    :param commit: The intel/llvm commit the adapter was built from.
    """
    def mutate(stamp: dict) -> None:
        existing = stamp.get("adapters")
        adapters = dict(existing) if isinstance(existing, dict) else {}
        adapters[vendor] = commit
        stamp["adapters"] = adapters
    _rewrite_stamp(root, mutate)


def toolchain_adapter_commit(root: Path, vendor: str) -> str | None:
    """Return the commit recorded for *vendor*'s adapter, or None.

    :param root: Bundle root (the directory holding ``bin/`` and ``lib/``).
    :param vendor: The backend's own vendor name.
    """
    adapters = read_toolchain_stamp(root).get("adapters")
    if not isinstance(adapters, dict):
        return None
    return adapters.get(vendor)


def has_sanitizer_runtime(root: Path) -> bool:
    """Report whether a SYCL bundle ships compiler-rt's sanitizer runtimes.

    A bundle without them compiles fine and only fails at *link* time, with a
    message naming a clang_rt library rather than the real cause, so this is
    probed directly: the answer decides whether an ASan build can work at all.
    Both compiler-rt layouts are covered — the per-target directory and the
    older ``lib/windows`` / ``lib/linux`` one.

    :param root: Bundle root (the directory holding ``bin/`` and ``lib/``).
    :return: True when at least one AddressSanitizer runtime library is present.
    """
    return any((root / "lib" / "clang").glob("*/lib/**/*clang_rt.asan*"))
