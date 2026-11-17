# install_context.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The state one installer run shares across its steps."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import final

from .config import ProvisionConfig
from .dependency_home import DEFAULT_HOME, DependencyHome
from .licence_consent import LicenceConsent
from .toolchain_selection import ToolchainSelection


@final
@dataclass
class InstallContext:
    """State shared across steps for one installer run."""

    cfg: ProvisionConfig
    selection: ToolchainSelection = field(default_factory=ToolchainSelection)
    #: The module name recorded in the registry.
    consumer: str = ""
    #: The command line the user runs; it words the messages that name it.
    program: str = ""
    #: The command that re-runs provisioning; empty means ``<program> setup``.
    rerun_command: str = ""
    #: A sentence the consumer adds to the note on removing the install; empty adds none.
    removal_hint: str = ""
    #: A sentence the consumer adds when AdaptiveCpp alone was selected and did not install.
    fallback_hint: str = ""
    #: The command that replaces a stale intel/llvm bundle; empty names the refresh option only.
    refresh_command: str = ""
    dry_run: bool = False
    #: The home whose dependency root the steps of this run read.
    home: DependencyHome = DEFAULT_HOME
    #: The run's licence consent; installers that accept a licence read it, None means none given.
    consent: LicenceConsent | None = None
    everything: bool = False
    #: The toolchain ConfigureStep pins as the default, or None to leave it.
    active_toolchain: str | None = None
    #: Whether to re-download a toolchain that is already present.
    refresh_toolchains: bool = False
    #: Whether the user has consented to the heavy Windows LLVM download.
    assume_acpp_llvm: bool = False
    #: The discrete-GPU vendor: nvidia, amd, intel, or none.
    gpu_vendor: str = ""
    #: Non-fatal problems surfaced by any step.
    warnings: list[str] = field(default_factory=list)
    #: Populated by DetectStep: tool/dependency name -> present?
    detected: dict[str, bool] = field(default_factory=dict)
    #: Populated by InstallDepsStep: package names actually installed this run.
    installed: list[str] = field(default_factory=list)
    #: Populated by ConfigureStep: config field name -> resolved absolute path.
    resolved_paths: dict[str, str] = field(default_factory=dict)

    @property
    def gpu(self) -> bool:
        """Report whether this run provisions the GPU toolkit."""
        return self.selection.gpu
