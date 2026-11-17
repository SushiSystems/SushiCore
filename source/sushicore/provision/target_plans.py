# target_plans.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds the plan each target registered for one dispatch, filled by the plan modules themselves."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Callable, Generic, TypeVar, final

from ..errors import SushiCoreError
from .target import ITarget

P = TypeVar("P")


class TargetPlanError(SushiCoreError):
    """Raised when a target has no plan, or a second plan for one target is registered."""


@final
class TargetPlans(Generic[P]):
    """Maps a target's name to the plan, or the factory of the plan, the modules of one package registered for it."""

    def __init__(self, package: str) -> None:
        """Bind the registry to the package whose modules register the plans.

        Args:
            package: The dotted name of the package holding one plan module per target.
        """
        self._package = package
        self._plans: dict[str, Callable[..., P]] = {}
        self._loaded = False

    def register(self, kind: str, plan: P) -> None:
        """Record *plan* as the plan of the target named *kind*.

        Raises:
            TargetPlanError: A plan is already registered for *kind*.
        """
        self.register_factory(kind, lambda **dependencies: plan)

    def register_factory(self, kind: str, factory: Callable[..., P]) -> None:
        """Record *factory* as what builds the plan of the target named *kind*.

        The factory is called with the dependencies :meth:`plan_for` is given, as keywords; a
        plan class whose constructor takes them as keywords is a factory.

        Raises:
            TargetPlanError: A plan is already registered for *kind*.
        """
        if kind in self._plans:
            raise TargetPlanError(f"{self._package} registers a second plan for {kind}")
        self._plans[kind] = factory

    def plan_for(self, target: ITarget, **dependencies: object) -> P:
        """Return the plan registered for *target*, importing the package's modules on first use.

        Args:
            dependencies: What the plan is built with, such as ``home``; one passed as ``None``
                is left to the plan's own default. A plan registered as an instance ignores them.

        Raises:
            TargetPlanError: No module of the package registered a plan for *target*.
        """
        self._load()
        if target.name not in self._plans:
            raise TargetPlanError(f"{self._package} has no plan for {target.name}")
        given = {name: value for name, value in dependencies.items() if value is not None}
        return self._plans[target.name](**given)

    def _load(self) -> None:
        """Import every module of the package once, so each registers its plan."""
        if self._loaded:
            return
        package = importlib.import_module(self._package)
        for module in sorted(pkgutil.iter_modules(package.__path__), key=lambda info: info.name):
            importlib.import_module(f"{self._package}.{module.name}")
        self._loaded = True
