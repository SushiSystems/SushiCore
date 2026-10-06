# selection.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Decides which toolchain components one provisioning run installs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .fragments import SHARED_OWNER, IDependencySource
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


def enabled_keys(chosen: ToolchainSelection) -> list[str]:
    """Return the key of every component *chosen* turns on, in table order."""
    return [component.key for component in COMPONENTS if getattr(chosen, component.field)]


def groups(source: IDependencySource) -> dict[str, list[str]]:
    """Return the toolchain keys modules declare, by capability, in declaration order."""
    found: dict[str, list[str]] = {}
    for dep in source.all():
        if dep.name in toolchain_keys() and dep.owner != SHARED_OWNER:
            found.setdefault(dep.provides or dep.name, []).append(dep.name)
    return found


def required_groups(source: IDependencySource) -> dict[str, list[str]]:
    """Return the capabilities of :func:`groups` that hold a required dependency."""
    required = {dep.name for dep in source.all() if dep.required}
    return {capability: members for capability, members in groups(source).items()
            if required.intersection(members)}


def derive(source: IDependencySource, present: Mapping[str, bool], *,
           requested: Sequence[str] = (), gpu: bool = True) -> ToolchainSelection:
    """Return the components to install for *source* on a machine holding *present*.

    Args:
        source: The declared dependencies.
        present: Toolchain key to whether the machine already has it.
        requested: Keys to install whatever the machine has. An optional
            toolchain installs only this way.
        gpu: Whether the run may provision the detected GPU's toolkit; it does only
            when some declared dependency is ``gpu_only``.

    Raises:
        ValueError: *requested* holds a key no component carries.
    """
    unknown = [key for key in requested if key not in toolchain_keys()]
    if unknown:
        raise ValueError(
            f"Unknown toolchain '{unknown[0]}'; choose one of: {', '.join(toolchain_keys())}.")
    chosen = {members[0] for members in required_groups(source).values()
              if not any(present.get(member) for member in members)}
    chosen.update(requested)
    values = {_FIELD[key]: True for key in chosen}
    values[_FIELD[GPU_KEY]] = gpu and any(dep.gpu_only for dep in source.all())
    return ToolchainSelection(**values)
