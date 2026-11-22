# panels.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Names the help panels of a Sushi CLI, the panel of each canonical verb and the one domain panel."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Optional, final

from . import verbs
from .errors import DomainPanelError, UnknownVerbError

K_BUILD_PANEL = "Build"
K_RUN_PANEL = "Run"
K_ENVIRONMENT_PANEL = "Environment"
K_RECORDS_PANEL = "Records"

#: The canonical panels, in the order a help page shows them; a domain panel sits after Run.
K_PANELS = (K_BUILD_PANEL, K_RUN_PANEL, K_ENVIRONMENT_PANEL, K_RECORDS_PANEL)

#: The panel each canonical verb is listed under.
K_VERB_PANELS = MappingProxyType({
    verbs.K_BUILD: K_BUILD_PANEL,
    verbs.K_TEST: K_BUILD_PANEL,
    verbs.K_CHECK: K_BUILD_PANEL,
    verbs.K_CLEAN: K_BUILD_PANEL,
    verbs.K_PACKAGE: K_BUILD_PANEL,
    verbs.K_DOCS: K_BUILD_PANEL,
    verbs.K_RUN: K_RUN_PANEL,
    verbs.K_BENCH: K_RUN_PANEL,
    verbs.K_SETUP: K_ENVIRONMENT_PANEL,
    verbs.K_DOCTOR: K_ENVIRONMENT_PANEL,
    verbs.K_LINK: K_ENVIRONMENT_PANEL,
    verbs.K_UNLINK: K_ENVIRONMENT_PANEL,
    verbs.K_CONFIG: K_ENVIRONMENT_PANEL,
    verbs.K_ENV: K_ENVIRONMENT_PANEL,
    verbs.K_WHERE: K_ENVIRONMENT_PANEL,
    verbs.K_STATUS: K_ENVIRONMENT_PANEL,
    verbs.K_BACKLOG: K_RECORDS_PANEL,
    verbs.K_DESIGN: K_RECORDS_PANEL,
})


def panel_of(verb: str) -> str:
    """Returns the panel the canonical *verb* is listed under.

    Raises:
        UnknownVerbError: *verb* is not a canonical verb.
    """
    if verb not in K_VERB_PANELS:
        raise UnknownVerbError(f"{verb!r} is not a canonical verb.")
    return K_VERB_PANELS[verb]


@final
@dataclass(frozen=True)
class CommandPanels:
    """The panels one CLI shows: the canonical four and at most one panel of its own domain.

    Args:
        domain: The panel the CLI's own commands go in, such as ``Models``; None when it has none.

    Raises:
        DomainPanelError: *domain* is empty or is the name of a canonical panel.
    """

    domain: Optional[str] = None

    def __post_init__(self) -> None:
        """Refuses a domain panel that is empty or repeats a canonical one."""
        if self.domain is not None and (not self.domain.strip() or self.domain in K_PANELS):
            raise DomainPanelError(
                f"the domain panel {self.domain!r} must be a name other than {', '.join(K_PANELS)}.")

    def order(self) -> tuple[str, ...]:
        """Returns the panels in the order the CLI registers their first command."""
        domain = () if self.domain is None else (self.domain,)
        return (K_BUILD_PANEL, K_RUN_PANEL, *domain, K_ENVIRONMENT_PANEL, K_RECORDS_PANEL)
