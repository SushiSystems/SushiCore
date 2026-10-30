# command_groups.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Names the command groups a CLI adds beside its own commands, and checks that it exposes them."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    import typer

K_BACKLOG = "backlog"
K_DESIGN = "design"

#: The groups a CLI built on this package carries, in the order the registering functions add them.
K_GROUPS = (K_BACKLOG, K_DESIGN)


def exposed_groups(app: "typer.Typer") -> frozenset[str]:
    """Returns the names of the command groups and commands the top level of *app* answers to.

    An app with one command and no callback is a single command, not a group, and answers to none.
    """
    import typer.main

    return frozenset(getattr(typer.main.get_command(app), "commands", {}))


def missing_groups(app: "typer.Typer", groups: Iterable[str] = K_GROUPS) -> list[str]:
    """Returns the groups among *groups* that *app* does not expose, in the order given."""
    exposed = exposed_groups(app)
    return [name for name in groups if name not in exposed]
