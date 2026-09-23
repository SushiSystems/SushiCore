# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The ``setup``, ``doctor``, ``link`` and ``unlink`` commands shared by every module CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from ..profile import ModuleProfile
from ..workspace import (
    WORKSPACE_MARKER,
    has_marker,
    remove_module,
    resolve_env_path,
    walk_up,
    write_module,
)
from . import home
from ._output import bind_console
from .checks import standard_checks
from .config import ProvisionConfig
from .doctor import Check, Doctor
from .fragments import TomlDependencySource
from .lock import LockTimeout, ProvisionLock
from .packages import (
    AptManager,
    DirectDownloadWindowsManager,
    DnfManager,
    IPackageManager,
    PacmanManager,
    VcpkgManager,
    WingetManager,
    YumManager,
    ZypperManager,
)
from .pipeline import InstallContext, InstallPipeline, ToolchainSelection
from .sinks import ModuleSink
from .steps import ConfigureStep, DetectStep, InstallDepsStep

#: Header written atop a module's ``config.local.toml``.
_MODULE_SINK_HEADER = [
    "# Auto-generated. Machine-specific tool paths for this module.",
    "# Safe to edit; re-running `setup` backs this up first.",
]


@dataclass(frozen=True)
class ModuleProvision:
    """What one module CLI hands the shared commands."""

    profile: ModuleProfile
    project_root: Callable[[], Path]
    load_config: Callable[[], ProvisionConfig]
    console: Callable[[], object]
    extra_checks: Callable[[], list[Check]] = lambda: []
    fragment: str = "cli/sushistack.deps.toml"


def _managers_for(cfg: ProvisionConfig) -> list[IPackageManager]:
    """Return the package managers this platform provisions dependencies through."""
    if cfg.is_windows:
        return [WingetManager(), DirectDownloadWindowsManager(), VcpkgManager(cfg)]
    # VcpkgManager also serves Linux: it is the only route for ports with no apt
    # package at all.
    return [AptManager(), DnfManager(), YumManager(), PacmanManager(), ZypperManager(),
            VcpkgManager(cfg)]


def _run_doctor(module: ModuleProvision, groups: Optional[set[str]]) -> int:
    """Run this module's checks, render the report, and return its process exit code."""
    cfg = module.load_config()
    fix = f"{module.profile.program} setup"
    checks = standard_checks(cfg, fix=fix) + module.extra_checks()
    doctor = Doctor(checks)
    report = doctor.run(groups)
    doctor.render(report, module.console())
    return report.exit_code()


def _resolve_workspace(explicit: Optional[Path], project_root: Path) -> Optional[Path]:
    """Return the workspace root: ``--workspace``, then ``SUSHISTACK_HOME``, then a walk-up."""
    if explicit is not None:
        return explicit
    env = resolve_env_path("SUSHISTACK_HOME")
    if env is not None:
        return env
    return walk_up(project_root, has_marker(WORKSPACE_MARKER))


def _no_workspace_message() -> str:
    """Return the error shown when no workspace can be resolved."""
    return (
        "No workspace found: pass --workspace, set SUSHISTACK_HOME, or run inside a "
        f"directory with a {WORKSPACE_MARKER} ancestor."
    )


def register_provision_commands(app: "typer.Typer", module: ModuleProvision) -> None:
    """Add ``setup``, ``doctor``, ``link`` and ``unlink`` to *app*."""
    import typer

    @app.command()
    def setup(
        dry_run: bool = typer.Option(False, "--dry-run", help="Show, don't change."),
        yes: bool = typer.Option(
            False, "--yes", help="Assume yes on the LLVM-download prompt, for unattended runs."),
    ) -> None:
        """Provision this module's dependencies, then report readiness."""
        bind_console(module.console)
        console = module.console()
        root = module.project_root()
        cfg = module.load_config()
        source = TomlDependencySource([(root / module.fragment, module.profile.name)])
        sink = ModuleSink(root / "cli", _MODULE_SINK_HEADER)
        pipeline = InstallPipeline([
            DetectStep(source, _managers_for(cfg)),
            InstallDepsStep(source, _managers_for(cfg)),
            ConfigureStep(sink),
        ])
        ctx = InstallContext(
            cfg=cfg,
            selection=ToolchainSelection(),
            consumer=module.profile.name,
            dry_run=dry_run,
            assume_acpp_llvm=yes,
        )
        try:
            with ProvisionLock(home.root() / ".lock"):
                ok = pipeline.run(ctx)
        except LockTimeout as exc:
            console.error(str(exc))
            raise typer.Exit(1)
        if not ok:
            raise typer.Exit(1)
        raise typer.Exit(_run_doctor(module, None))

    @app.command()
    def doctor(
        for_group: Optional[str] = typer.Option(
            None, "--for", help="Restrict the report to one check group."),
    ) -> None:
        """Report on this machine's readiness to build the module."""
        bind_console(module.console)
        groups = {for_group} if for_group else None
        raise typer.Exit(_run_doctor(module, groups))

    @app.command()
    def link(
        workspace: Optional[Path] = typer.Option(
            None, "--workspace", help="Workspace root to register this module in."),
    ) -> None:
        """Record this module's location in a workspace's module registry."""
        bind_console(module.console)
        console = module.console()
        root = module.project_root()
        target = _resolve_workspace(workspace, root)
        if target is None:
            console.error(_no_workspace_message())
            raise typer.Exit(2)
        write_module(target, module.profile.name, root)
        console.success(f"Linked {module.profile.name} into {target}.")

    @app.command()
    def unlink(
        workspace: Optional[Path] = typer.Option(
            None, "--workspace", help="Workspace root to remove this module from."),
    ) -> None:
        """Remove this module's entry from a workspace's module registry."""
        bind_console(module.console)
        console = module.console()
        root = module.project_root()
        target = _resolve_workspace(workspace, root)
        if target is None:
            console.error(_no_workspace_message())
            raise typer.Exit(2)
        removed = remove_module(target, module.profile.name)
        if removed:
            console.success(f"Unlinked {module.profile.name} from {target}.")
        else:
            console.info(f"{module.profile.name} was not linked into {target}.")
