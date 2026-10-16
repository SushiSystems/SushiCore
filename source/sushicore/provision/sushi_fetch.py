# sushi_fetch.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The setup step that clones each pinned Sushi library no directory or sibling provides."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Sequence

from sushicore.deps_fragment import SushiPin

from ._output import console
from .git_client import IGitClient
from .pipeline import InstallContext, Step, StepResult
from .sushi_sources import SourceKind, directory_variable, fetched_dir, resolve

_log = logging.getLogger(__name__)

#: Where every Sushi library is cloned from; ``{name}`` is its lower-case name.
K_REPOSITORY_URL = "https://github.com/sushisystems/{name}.git"


class FetchSushiSourcesStep(Step):
    """Clones each pinned Sushi library at its tag and refuses a commit off the pin."""

    name = "fetch Sushi libraries"

    def __init__(self, root: Path, pins: Sequence[SushiPin], git: IGitClient) -> None:
        """Hold the consumer's checkout *root*, its *pins*, and the *git* to clone with."""
        self._root = root
        self._pins = list(pins)
        self._git = git

    def run(self, ctx: InstallContext) -> StepResult:
        """Fetch every pin that needs it; FAILED on the first clone or commit that fails."""
        fetched = 0
        for pin in self._pins:
            found = resolve(self._root, pin.name, pin.version)
            if found is not None and found.kind is not SourceKind.FETCHED:
                _log.info("%s comes from the %s %s", pin.name, found.kind.value, found.path)
                continue
            if found is not None and self._git.head(found.path) == pin.commit:
                continue
            if not self._fetch(pin, ctx.dry_run):
                return StepResult.FAILED
            fetched += 1
        return StepResult.OK if fetched else StepResult.SKIPPED

    def _fetch(self, pin: SushiPin, dry_run: bool) -> bool:
        """Clone *pin* into its folder and keep it only when HEAD is the pinned commit."""
        destination = fetched_dir(pin.name, pin.version)
        if destination.exists() and not dry_run:
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        url = K_REPOSITORY_URL.format(name=pin.name)
        if not self._git.clone_tag(url, pin.version, destination, dry_run):
            console.error(f"Fetching {pin.name} {pin.version} failed: git could not clone the "
                          f"tag {pin.version} of {url}. Clone it yourself and set "
                          f"{directory_variable(pin.name)} to the checkout.")
            shutil.rmtree(destination, ignore_errors=True)
            return False
        if dry_run:
            return True
        head = self._git.head(destination)
        if head != pin.commit:
            shutil.rmtree(destination, ignore_errors=True)
            console.error(f"{pin.name} {pin.version} is at commit {head or '(unknown)'}, "
                          f"and the fragment pins {pin.commit}; the clone was removed.")
            return False
        _log.info("fetched %s %s into %s", pin.name, pin.version, destination)
        return True
