# amd_hardware.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""What the amdgpu kernel driver reports about this machine: the ISA of each AMD card.

The driver publishes one node per agent under ``/sys/class/kfd/kfd/topology/nodes``. Its
``gfx_target_version`` packs the ISA as ``major * 10000 + minor * 100 + stepping``, and the ISA
name spells minor and stepping in hexadecimal: 90010 is ``gfx90a``, 110003 is ``gfx1103``. A
CPU node reports 0. Nothing has to be installed to read it.
"""

from __future__ import annotations

import dataclasses
import logging
import re
import typing
from pathlib import Path

_log = logging.getLogger(__name__)

#: Where the amdgpu driver lists its agents.
K_KFD_NODES = Path("/sys/class/kfd/kfd/topology/nodes")

K_TARGET_VERSION = re.compile(r"^gfx_target_version\s+(\d+)\s*$", re.MULTILINE)


@typing.final
@dataclasses.dataclass(frozen=True, slots=True)
class AmdHardware:
    """The AMD cards of a machine.

    Args:
        targets: Each distinct ISA, sorted: ``("gfx1030", "gfx1103")``.
    """

    targets: tuple[str, ...]

    def describe(self) -> str:
        """Return the cards for a console line."""
        return ", ".join(self.targets)

    def fingerprint(self) -> str:
        """Return a stable text that changes when a card does."""
        return f"gfx={','.join(self.targets)}"


def target_name(version: int) -> str:
    """Return the ISA name a ``gfx_target_version`` stands for, such as ``gfx90a``."""
    major, rest = divmod(version, 10000)
    minor, stepping = divmod(rest, 100)
    return f"gfx{major}{minor:x}{stepping:x}"


def parse_targets(properties: typing.Iterable[str]) -> AmdHardware | None:
    """Build the record from the text of each node's ``properties``, or None without a card."""
    targets = {target_name(int(m.group(1))) for text in properties
               for m in K_TARGET_VERSION.finditer(text) if int(m.group(1))}
    return AmdHardware(tuple(sorted(targets))) if targets else None


def query_hardware(nodes: Path = K_KFD_NODES) -> AmdHardware | None:
    """Read the driver's topology; None when there is no amdgpu driver or no AMD card."""
    try:
        texts = [path.read_text(encoding="utf-8") for path in nodes.glob("*/properties")]
    except OSError as error:
        _log.info("%s could not be read (%s: %s)", nodes, type(error).__name__, error)
        return None
    return parse_targets(texts)
