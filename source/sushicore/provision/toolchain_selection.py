# toolchain_selection.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Which toolchain components one provisioning run installs."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import final


@final
@dataclass(frozen=True)
class ToolchainSelection:
    """Which of the four customizable toolchain components a run provisions."""

    install_intel_llvm: bool = False
    install_acpp: bool = False
    oneapi: bool = False
    gpu: bool = False

    def as_dict(self) -> dict[str, bool]:
        """Return the selection as field name -> value."""
        return {f.name: bool(getattr(self, f.name)) for f in fields(self)}

    def merged(self, overrides: dict[str, bool]) -> "ToolchainSelection":
        """Return a copy with the known field names in *overrides* applied."""
        values = self.as_dict()
        values.update({k: bool(v) for k, v in overrides.items() if k in values})
        return ToolchainSelection(**values)
