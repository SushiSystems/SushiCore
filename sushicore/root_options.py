# root_options.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The options every Sushi CLI answers before any command: ``--version`` and ``--describe``.

:func:`register_root_options` gives a CLI both with one call. A CLI that needs a root option
of its own builds its callback from :func:`version_option` and :func:`describe_option`.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Callable, Optional, Sequence

from .describe import catalogue, installed_version

if TYPE_CHECKING:
    import typer

K_UNKNOWN = "unknown"
K_VERSION_HELP = "Print the CLI's version and exit."
K_DESCRIBE_HELP = "Print the command catalogue as JSON and exit."


def version_line(distribution: str) -> str:
    """Returns the distribution name and its installed version, or ``unknown``."""
    return f"{distribution} {installed_version(distribution) or K_UNKNOWN}"


def version_option(lines: Callable[[], Sequence[str]], *, help: str = K_VERSION_HELP) -> Any:
    """Returns the default of a ``--version`` parameter that prints *lines* and exits 0."""
    import typer

    def show(requested: Optional[bool]) -> None:
        """Prints the version lines and exits when the flag was given."""
        if not requested:
            return
        for line in lines():
            typer.echo(line)
        raise typer.Exit(0)

    return typer.Option(None, "--version", callback=show, is_eager=True, help=help)


def describe_option(
    app: "typer.Typer", *, distribution: str, applies_to: Sequence[str] = (),
    help: str = K_DESCRIBE_HELP,
) -> Any:
    """Returns the default of a ``--describe`` parameter that prints the catalogue and exits 0."""
    import typer

    def show(requested: Optional[bool]) -> None:
        """Prints the catalogue and exits when the flag was given."""
        if not requested:
            return
        document = catalogue(app, distribution=distribution, applies_to=applies_to)
        typer.echo(json.dumps(document, indent=2))
        raise typer.Exit(0)

    return typer.Option(None, "--describe", callback=show, is_eager=True, help=help)


def register_root_options(
    app: "typer.Typer", *, distribution: str,
    version_lines: Callable[[], Sequence[str]] | None = None,
) -> None:
    """Adds ``--version`` and ``--describe`` to *app*, keeping its help text.

    Args:
        app: The application; it must not have a callback of its own.
        distribution: The distribution name in the CLI's ``pyproject.toml``.
        version_lines: What ``--version`` prints; one line naming the distribution and its
            version when None.
    """
    lines = version_lines or (lambda: [version_line(distribution)])

    @app.callback(help=app.info.help)
    def root(
        show_version: Optional[bool] = version_option(lines),
        describe: Optional[bool] = describe_option(app, distribution=distribution),
    ) -> None:
        """Answers the root options; a command runs after it."""
