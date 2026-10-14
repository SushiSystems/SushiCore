# cuda_choice_file.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reads and writes the recorded CUDA choice, so a later run with the same cards and driver
reuses it without reading NVIDIA's index again.

The file format is in docs/design/CUDA_TOOLKIT_SELECTION.md, section "The choice file".
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os
import typing
from pathlib import Path

from .cuda_choice import CudaChoice

K_LOGGER = logging.getLogger("sushicore.provision")

#: The version of the file's layout; a different value is ignored.
K_FORMAT = 1


@typing.final
class CudaChoiceFile:
    """Reads and writes the recorded choice at one path.

    Args:
        path: The JSON file.
    """

    def __init__(self, path: Path) -> None:
        """Store the file's path."""
        self._path = path

    def read(self) -> CudaChoice | None:
        """Return the recorded choice, or None when there is none usable."""
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as error:
            K_LOGGER.warning("%s is unreadable (%s); the CUDA release is chosen again",
                             self._path, error)
            return None
        if not isinstance(data, dict) or data.get("format") != K_FORMAT:
            return None
        try:
            return CudaChoice(str(data["fingerprint"]), str(data["platform"]),
                              str(data["release"]))
        except KeyError as error:
            K_LOGGER.warning("%s lacks %s; the CUDA release is chosen again", self._path, error)
            return None

    def write(self, choice: CudaChoice) -> None:
        """Record *choice*, replacing the file in one step."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        part = self._path.with_name(self._path.name + ".part")
        part.write_text(json.dumps({"format": K_FORMAT, **dataclasses.asdict(choice)},
                                   indent=2) + "\n", encoding="utf-8")
        os.replace(part, self._path)
