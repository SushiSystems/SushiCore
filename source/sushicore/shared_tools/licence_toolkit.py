# licence_toolkit.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Loads the license block writer of a SushiCore tag, so the blocks follow the release being synced."""

from __future__ import annotations

import importlib
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import final

from .git_reader import GitReader

K_FOLDER = "tools"


@final
@dataclass(frozen=True, slots=True)
class LicenceToolkit:
    """The names of the writer in the tag's `tools/` that the sync uses."""

    header: type
    licence: type
    from_module: object
    is_source: object
    rewrite: object


def _top_level_names(tools: Path) -> set[str]:
    """Returns the importable top-level names a `tools/` folder holds."""
    return {entry.stem if entry.is_file() else entry.name for entry in tools.iterdir()}


@contextmanager
def load_toolkit(reader: GitReader, tag: str) -> Iterator[LicenceToolkit]:
    """Yields the writer of the tag's `tools/`, and leaves `sys.path` and `sys.modules` as they were."""
    with tempfile.TemporaryDirectory() as scratch:
        reader.extract(tag, K_FOLDER, Path(scratch))
        tools = Path(scratch) / K_FOLDER
        names = _top_level_names(tools)
        shadowed = {key: module for key, module in sys.modules.items() if key.partition(".")[0] in names}
        for key in shadowed:
            del sys.modules[key]
        saved_path = list(sys.path)
        sys.path.insert(0, str(tools))
        try:
            writer: ModuleType = importlib.import_module("licensing.write_license_block")
            licence: ModuleType = importlib.import_module("documentation.licence")
            yield LicenceToolkit(
                writer.Header, licence.Licence, licence.from_module, writer.is_source, writer.rewrite
            )
        finally:
            sys.path[:] = saved_path
            for key in [key for key in sys.modules if key.partition(".")[0] in names]:
                del sys.modules[key]
            sys.modules.update(shadowed)
