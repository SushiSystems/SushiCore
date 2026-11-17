# winget.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The Windows winget package manager."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from typing import Any

from sushicore.proc import CommandRunner

from ..licence_consent import Licence, LicenceConsent, is_accepted
from ..process_run import provision_runner
from .base import IPackageManager
from .winget_licence import read_licence


class WingetManager(IPackageManager):
    """Installs Windows system toolchain packages through winget."""

    name = "winget"

    def __init__(self, consent: LicenceConsent | None = None, *, console: Any,
                 show: Callable[[list[str]], str] | None = None,
                 runner: CommandRunner | None = None) -> None:
        """Store the run's consent, the runner of the winget commands and the licence reader.

        Without consent no install runs.

        Args:
            consent: The run's licence consent.
            show: Returns what a ``winget show`` command prints; reads it through *runner* when
                ``None``.
            console: The console the manager and its runner print through.
            runner: Runs the winget commands; the provision runner on *console* when ``None``.
        """
        super().__init__(console=console)
        self._consent = consent
        self._runner = runner or provision_runner(console)
        self._show = show or self._read_output
        self._licences: dict[str, Licence] = {}

    def _read_output(self, command: list[str]) -> str:
        """Run *command* and return what it printed; an empty text when it cannot start."""
        try:
            return self._runner.capture(command)[1]
        except OSError:
            return ""

    def licence_of(self, pkg: str) -> Licence:
        """Returns the licence of *pkg*, named by its id and linked to its own licence page."""
        if pkg not in self._licences:
            self._licences[pkg] = read_licence(pkg, self._show)
        return self._licences[pkg]

    def available(self) -> bool:
        """Report whether ``winget`` is on PATH."""
        return shutil.which("winget") is not None

    def is_installed(self, pkg: str) -> bool:
        """Report whether winget lists *pkg* as installed."""
        try:
            code, output, _error = self._runner.capture(["winget", "list", "--id", pkg, "-e"])
        except OSError:
            return False
        listed = {word.lower() for word in output.split()}
        return code == 0 and pkg.lower() in listed

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Install each of *pkgs* through ``winget install`` once the user accepted its agreements.

        Returns:
            False unless the consent covers the licence of every package; nothing is installed
            then. A dry run installs nothing and asks no consent.
        """
        refused = [] if dry_run else [
            held for held in map(self.licence_of, pkgs) if not is_accepted(self._consent, held)]
        if refused:
            self._console.error("winget installs nothing without consent to: "
                          + ", ".join(f"{held.name} ({held.link})" for held in refused))
            return False
        ok = True
        for pkg in pkgs:
            rc = self._runner.run_drained(
                ["winget", "install", "--id", pkg, "-e",
                 "--accept-package-agreements", "--accept-source-agreements",
                 "--silent"],
                None, dry_run=dry_run, check=True,
            )
            ok = ok and rc == 0
        return ok

    def remove(self, pkgs: list[str], dry_run: bool) -> bool:
        """Uninstall each of *pkgs* through ``winget uninstall``."""
        ok = True
        for pkg in pkgs:
            rc = self._runner.run_drained(
                ["winget", "uninstall", "--id", pkg, "-e", "--silent"],
                None, dry_run=dry_run,
            )
            ok = ok and rc == 0
        return ok
