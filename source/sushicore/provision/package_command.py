# package_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Registers the shared ``package`` command that every Sushi library CLI offers."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from ._output import bind_console
from .commands import ModuleProvision
from .package_install import PackageInstaller, run_command

#: The build tree the command installs from unless told otherwise.
K_DEFAULT_BUILD_DIR = "build"

#: Where the install goes unless told otherwise, below the checkout.
K_DEFAULT_PREFIX = "build/dist"


def register_package_command(app: "typer.Typer", module: ModuleProvision,
                             run: Callable[..., int] = run_command) -> None:
    """Add ``package`` to *app*: install a built tree to a prefix, then archive it with CPack.

    The command installs; it does not check what it installs.

    Args:
        app: The CLI's Typer application.
        module: What the CLI hands the shared commands; its config names the cmake executable.
        run: Runs a command in a folder; replaced in tests.
    """
    import typer

    program = module.profile.program
    epilog = "\n".join((
        f"{program} package",
        f"{program} package --build-dir build/pkg-x --prefix ../staging --no-archive",
        f"{program} package --prefix ../staging --force  # Clear a folder {program} did not stage",
    ))

    @app.command("package", rich_help_panel=module.panel, epilog=epilog)
    def package(
        build_dir: str = typer.Option(
            K_DEFAULT_BUILD_DIR, "--build-dir", help="The built tree to install from."),
        prefix: Optional[str] = typer.Option(
            None, "--prefix",
            help=f"Where to install; the folder is emptied first. Defaults to {K_DEFAULT_PREFIX}."),
        no_archive: bool = typer.Option(
            False, "--no-archive", help="Install only; do not run CPack."),
        force: bool = typer.Option(
            False, "--force", help="Clear a --prefix that holds files this command did not stage."),
    ) -> None:
        """Install the built tree to a prefix and archive it for redistribution."""
        bind_console(module.console)
        cfg = module.load_config()
        cmake = cfg.expand(cfg.cmake_exe) if cfg.cmake_exe else "cmake"
        installer = PackageInstaller(module.console(), cmake, run)
        raise typer.Exit(installer.install(
            module.project_root(), Path(build_dir), Path(prefix or K_DEFAULT_PREFIX),
            archive=not no_archive, force=force))
