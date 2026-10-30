# commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Registers the ``setup``, ``doctor``, ``link`` and ``unlink`` commands every module CLI shares.

Each command body lives in its own module; this one declares their options and ends every command
with one ``result`` event.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from . import selection
from ._output import bind_console
from .doctor import GROUPS
from .doctor_command import run_doctor
from .link_command import run_link, run_unlink
from .module_provision import ModuleProvision
from .outcome import K_EXIT_USAGE, finish
from .setup_command import run_setup

__all__ = ["ModuleProvision", "register_provision_commands"]


def register_provision_commands(app: "typer.Typer", module: ModuleProvision) -> None:
    """Add the four provision commands to *app*, or ``doctor`` alone to a binary install."""
    import typer

    program = module.profile.program

    def command(*examples: str):
        """Return the decorator registering a command under the module's panel with *examples*."""
        epilog = "\n".join(f"{program} {example}" for example in examples)
        return app.command(rich_help_panel=module.panel, epilog=epilog)

    binary = module.is_binary()

    if not binary:
        @command("setup", "setup --dry-run  # Show what would be installed",
                 "setup --toolchain adaptivecpp  # Also install a second SYCL toolchain")
        def setup(
            dry_run: bool = typer.Option(False, "--dry-run", help="Show, don't change."),
            yes: bool = typer.Option(
                False, "--yes", "-y", help="Assume yes on the LLVM-download prompt, for unattended runs."),
            toolchain: Optional[list[str]] = typer.Option(
                None, "--toolchain",
                help="Also install this toolchain: "
                     + " | ".join(selection.toolchain_keys()) + ". Repeatable."),
            no_gpu: bool = typer.Option(
                False, "--no-gpu", help="Skip the toolkit for this machine's GPU."),
        ) -> None:
            """Provision what this module needs to build, then report readiness."""
            bind_console(module.console)
            raise typer.Exit(finish(module.console(), run_setup(
                module, dry_run=dry_run, yes=yes, toolchains=toolchain or (), gpu=not no_gpu)))

    known_groups = (*GROUPS, *(name for name in module.groups if name not in GROUPS))

    @command("doctor", "doctor --for build  # Only the checks a build needs")
    def doctor(
        for_group: Optional[str] = typer.Option(
            None, "--for", help="Restrict the report to one check group: " + " | ".join(known_groups) + "."),
    ) -> None:
        """Report on this machine's readiness to build the module."""
        bind_console(module.console)
        console = module.console()
        if for_group is not None and for_group not in known_groups:
            console.error(
                f"Unknown check group '{for_group}'; choose one of: {', '.join(known_groups)}.")
            raise typer.Exit(K_EXIT_USAGE)
        groups = {for_group} if for_group else None
        raise typer.Exit(finish(console, run_doctor(module, groups)))

    if binary:
        return

    @command("link", "link --workspace ~/sushi  # Name the workspace instead of finding it")
    def link(
        workspace: Optional[Path] = typer.Option(
            None, "--workspace", help="Workspace root to register this module in."),
    ) -> None:
        """Record this module's location in a workspace's module registry."""
        bind_console(module.console)
        raise typer.Exit(finish(module.console(), run_link(module, workspace)))

    @command("unlink")
    def unlink(
        workspace: Optional[Path] = typer.Option(
            None, "--workspace", help="Workspace root to remove this module from."),
    ) -> None:
        """Remove this module's entry from a workspace's module registry."""
        bind_console(module.console)
        raise typer.Exit(finish(module.console(), run_unlink(module, workspace)))
