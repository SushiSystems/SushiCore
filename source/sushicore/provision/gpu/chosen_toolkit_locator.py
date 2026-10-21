# chosen_toolkit_locator.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Locates and provisions any vendor's toolkit by the release its hardware needs.

The flow is the same for every vendor: read the cards, reuse the release recorded for them or
choose one, install it under the user's home, and name its root in the vendor's variable. The
vendor answers each step; this class owns only the order. The reasoning is in
docs/design/GPU_TOOLKIT_SELECTION/README.md.
"""

from __future__ import annotations

import os
import pathlib
import typing

from .._output import console
from ..user_environment import UserEnvironment, read_user_variable, write_user_variable
from .backend import ToolkitInstall
from .gpu_hardware import GpuHardware
from .toolkit_choice import ToolkitChoice
from .toolkit_choice_file import ToolkitChoiceFile
from .toolkit_vendor import ToolkitSourceError, ToolkitVendor

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig


@typing.final
class ChosenToolkitLocator:
    """A :class:`ToolkitLocator` whose release is chosen from the hardware.

    Args:
        vendor: Answers every vendor-specific question.
        choices: The record of the last choice; ``<toolkits_dir>/choice.json`` when None.
        environment: The user's persistent variables; the platform's default when None.
    """

    def __init__(self, vendor: ToolkitVendor, choices: ToolkitChoiceFile | None = None,
                 environment: UserEnvironment | None = None) -> None:
        """Store the vendor and where the choice and the root variable are kept."""
        self._vendor = vendor
        self._choices = choices
        self._environment = environment

    def locate(self, cfg: "ProvisionConfig") -> ToolkitInstall | None:
        """Return the toolkit the root variable names, in this process or the user's
        variables, else one installed by other means."""
        variable = self._vendor.root_variable
        for raw in (os.environ.get(variable, ""),
                    read_user_variable(variable, self._environment) or ""):
            if raw and self._vendor.is_toolkit_root(pathlib.Path(os.path.normpath(raw))):
                return ToolkitInstall(root=pathlib.Path(os.path.normpath(raw)), version=None)
        found = self._vendor.find_system_toolkit()
        return ToolkitInstall(root=found, version=None) if found is not None else None

    def provision(self, cfg: "ProvisionConfig", dry_run: bool) -> bool:
        """Install the release this machine needs and point the root variable at it.

        Always returns True: without a driver, a network or a fitting release the CPU path
        still builds, and the reason is reported.
        """
        name = self._vendor.name
        hardware = self._vendor.query_hardware()
        if hardware is None:
            console.warn(f"The driver reported no card; the {name} toolkit is not installed "
                         "and the build uses the CPU path.")
            return True
        console.info(f"{name} cards: {hardware.describe()}.")
        if dry_run:
            console.info(f"(dry-run) would choose the {name} release for this hardware and "
                         f"install it under {self._vendor.toolkits_dir}.")
            return True
        try:
            root = self._provide(hardware)
        except ToolkitSourceError as error:
            self._vendor.discard_downloads()
            self._report_failure(cfg, str(error))
            return True
        if root is None:
            return True
        variable = self._vendor.root_variable
        os.environ[variable] = str(root)
        write_user_variable(variable, str(root), self._environment)
        console.success(f"{name} toolkit at {root}; {variable} points to it.")
        return True

    def _provide(self, hardware: GpuHardware) -> pathlib.Path | None:
        """Return the root of the release to use, installing it when needed."""
        vendor = self._vendor
        override = os.environ.get(vendor.override_variable, "").strip()
        if override:
            label = vendor.resolve_override(override)
            console.info(f"{vendor.override_variable} asks for {vendor.name} {label}.")
            return self._install(label)
        choices = self._choices or ToolkitChoiceFile(vendor.toolkits_dir / "choice.json")
        recorded = choices.read()
        if (recorded is not None and recorded.fingerprint == hardware.fingerprint()
                and recorded.platform == vendor.platform_key
                and vendor.is_installed(recorded.release)):
            console.info(f"{vendor.name} {recorded.release} was chosen for this hardware "
                         "before.")
            return vendor.root_of(recorded.release)
        label = vendor.choose(hardware)
        if label is None:
            vendor.discard_downloads()
            console.warn(f"No published {vendor.name} release fits {hardware.describe()}; "
                         f"update the driver, or set {vendor.override_variable}. The build "
                         "uses the CPU path.")
            return None
        console.info(f"{vendor.name} {label} is the newest release that fits every card here.")
        root = self._install(label)
        choices.write(ToolkitChoice(hardware.fingerprint(), vendor.platform_key, label))
        return root

    def _install(self, label: str) -> pathlib.Path:
        """Install the release labelled *label* unless it is in place, and return its root."""
        vendor = self._vendor
        if vendor.is_installed(label):
            return vendor.root_of(label)
        console.info(f"Installing {vendor.name} {label} under {vendor.root_of(label)}.")
        return vendor.install(label)

    def _report_failure(self, cfg: "ProvisionConfig", reason: str) -> None:
        """Say why no release was installed and what the build uses instead."""
        existing = self.locate(cfg)
        fallback = (f"the toolkit at {existing.root} stays in use" if existing is not None
                    else "the build uses the CPU path")
        console.warn(f"{self._vendor.name} toolkit not installed: {reason}; {fallback}.")
