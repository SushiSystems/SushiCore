# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Decides which toolchain components one provisioning run installs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .fragments import IDependencySource
from .pipeline import ToolchainSelection


@dataclass(frozen=True)
class Component:
    """One heavy component a run can install, and the selection field it sets."""

    key: str
    label: str
    field: str


#: Key of the component that follows the machine, not a fragment.
GPU_KEY = "gpu"

COMPONENTS: tuple[Component, ...] = (
    Component("intel-llvm", "intel/llvm SYCL toolchain (clang++ -fsycl) — primary",
              "install_intel_llvm"),
    Component("adaptivecpp", "AdaptiveCpp (acpp) — secondary SYCL toolchain", "install_acpp"),
    Component("oneapi", "Intel oneAPI DPC++ (icx/icpx) — heavy, several GB", "oneapi"),
    Component(GPU_KEY, "Toolkit for this machine's GPU, detected automatically", "gpu"),
)

_FIELD = {component.key: component.field for component in COMPONENTS}


def toolchain_keys() -> tuple[str, ...]:
    """Return the key of every component a fragment can declare."""
    return tuple(component.key for component in COMPONENTS if component.key != GPU_KEY)


def groups(source: IDependencySource) -> list[list[str]]:
    """Return the declared toolchain keys grouped by capability, in declaration order."""
    groups: dict[str, list[str]] = {}
    for dep in source.all():
        if dep.name in toolchain_keys():
            groups.setdefault(dep.provides or dep.name, []).append(dep.name)
    return list(groups.values())


def derive(source: IDependencySource, present: Mapping[str, bool], *,
           requested: Sequence[str] = (), gpu: bool = True) -> ToolchainSelection:
    """Return the components to install for *source* on a machine holding *present*.

    Args:
        source: The declared dependencies.
        present: Toolchain key to whether the machine already has it.
        requested: Keys to install whatever the machine has.
        gpu: Whether the run provisions the detected GPU's toolkit.

    Raises:
        ValueError: *requested* holds a key no component carries.
    """
    unknown = [key for key in requested if key not in toolchain_keys()]
    if unknown:
        raise ValueError(
            f"Unknown toolchain '{unknown[0]}'; choose one of: {', '.join(toolchain_keys())}.")
    chosen = {members[0] for members in groups(source)
              if not any(present.get(member) for member in members)}
    chosen.update(requested)
    values = {_FIELD[key]: True for key in chosen}
    values[_FIELD[GPU_KEY]] = gpu
    return ToolchainSelection(**values)
