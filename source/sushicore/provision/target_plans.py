# target_plans.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds the plan each target registered for one dispatch, filled by the plan modules themselves."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Generic, TypeVar, final

from ..errors import SushiCoreError
from .target import ITarget

P = TypeVar("P")


class TargetPlanError(SushiCoreError):
    """Raised when a target has no plan, or a second plan for one target is registered."""


@final
class TargetPlans(Generic[P]):
    """Maps a target's name to the plan the modules of one package registered for it."""

    def __init__(self, package: str) -> None:
        """Bind the registry to the package whose modules register the plans.

        Args:
            package: The dotted name of the package holding one plan module per target.
        """
        self._package = package
        self._plans: dict[str, P] = {}
        self._loaded = False

    def register(self, kind: str, plan: P) -> None:
        """Record *plan* as the plan of the target named *kind*.

        Raises:
            TargetPlanError: A plan is already registered for *kind*.
        """
        if kind in self._plans:
            raise TargetPlanError(f"{self._package} registers a second plan for {kind}")
        self._plans[kind] = plan

    def plan_for(self, target: ITarget) -> P:
        """Return the plan registered for *target*, importing the package's modules on first use.

        Raises:
            TargetPlanError: No module of the package registered a plan for *target*.
        """
        self._load()
        if target.name not in self._plans:
            raise TargetPlanError(f"{self._package} has no plan for {target.name}")
        return self._plans[target.name]

    def _load(self) -> None:
        """Import every module of the package once, so each registers its plan."""
        if self._loaded:
            return
        package = importlib.import_module(self._package)
        for module in sorted(pkgutil.iter_modules(package.__path__), key=lambda info: info.name):
            importlib.import_module(f"{self._package}.{module.name}")
        self._loaded = True
