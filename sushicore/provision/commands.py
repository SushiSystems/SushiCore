# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The ``setup``, ``doctor``, ``link`` and ``unlink`` commands shared by every module CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

from ..profile import ModuleProfile
from ..workspace import (
    WORKSPACE_MARKER,
    LinkEditError,
    clear_link,
    has_marker,
    remove_module,
    resolve_env_path,
    walk_up,
    write_link,
    write_module,
)
from . import closure as closure_module
from . import home, manifests, probe, selection
from ._output import bind_console
from .checks import (
    capability_check,
    fragment_check,
    modules_check,
    python_check,
    stamp_check,
    standard_checks,
)
from .closure import Closure, Locate
from .config import ProvisionConfig
from .doctor import GROUPS, Check, Doctor
from .fragments import IDependencySource
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

#: Seconds ``setup`` waits for another process's ``ProvisionLock`` before giving up.
_LOCK_TIMEOUT = 600.0

#: Whether ``setup`` draws a progress bar around the pipeline.
_SHOW_PROGRESS = True


def _locate_nothing(name: str) -> Optional[Path]:
    """Report that the module *name* has no checkout."""
    del name
    return None


@dataclass(frozen=True)
class ModuleProvision:
    """What one module CLI hands the shared commands.

    Args:
        locate: Finds the checkout of a module the fragment's ``depends_on`` names.
        panel: The help panel the commands are listed under, or None for the default.
        is_binary: Reports a binary install, which registers ``doctor`` alone.
        uses_base: Whether the shared base fragment joins the module's own.
    """

    profile: ModuleProfile
    project_root: Callable[[], Path]
    load_config: Callable[[], ProvisionConfig]
    console: Callable[[], object]
    extra_checks: Callable[[], list[Check]] = lambda: []
    fragment: str = "cli/sushistack.deps.toml"
    locate: Locate = _locate_nothing
    panel: Optional[str] = None
    is_binary: Callable[[], bool] = lambda: False
    uses_base: bool = False


#: Exit code for a request ``setup`` cannot act on: an unknown toolchain, a missing module.
_EXIT_USAGE = 2


def _managers_for(cfg: ProvisionConfig) -> list[IPackageManager]:
    """Return the package managers this platform provisions dependencies through."""
    if cfg.is_windows:
        return [WingetManager(), DirectDownloadWindowsManager(), VcpkgManager(cfg)]
    return [AptManager(), DnfManager(), YumManager(), PacmanManager(), ZypperManager(),
            VcpkgManager(cfg)]


def _closure(module: ModuleProvision, root: Path) -> Closure:
    """Return the fragments *module* needs: the base when asked for, its modules', its own.

    Raises:
        ValueError: The modules depend on one another in a cycle.
    """
    shared = [(manifests.base_fragment(), manifests.BASE_OWNER)] if module.uses_base else []
    return closure_module.resolve(module.profile.key, root, module.locate,
                                  fragment=module.fragment, shared=shared)


def _source(module: ModuleProvision, root: Path, found: Closure) -> TomlDependencySource:
    """Return the dependency source over *found*, or over the module's own fragment path."""
    sources = list(found.sources) or [(root / module.fragment, module.profile.key)]
    return TomlDependencySource(sources)


def _present_toolchains(cfg: ProvisionConfig) -> dict[str, bool]:
    """Return each SYCL toolchain's key mapped to whether this machine holds it."""
    return {name: present for name, present, _detail in probe.toolchain_status(cfg, False)}


def _missing_module_message(module: str, wanted_by: str) -> str:
    """Return the line that tells a user where the checkout of *module* belongs."""
    return (f"{wanted_by} builds on {module}, and no checkout of it was found. "
            f"Clone it beside this repository or set {module.upper()}_DIR.")


def _checks(module: ModuleProvision, cfg: ProvisionConfig, source: IDependencySource,
            found: Closure) -> list[Check]:
    """Return every check ``doctor`` runs for a source checkout of *module*."""
    fix = f"{module.profile.program} setup"
    clone = "clone it beside this repository"
    return (standard_checks(cfg, fix=fix)
            + [modules_check(found.missing, clone),
               capability_check(source, _present_toolchains(cfg), fix),
               fragment_check(source, cfg.platform, False, fix),
               stamp_check(home.root())]
            + module.extra_checks())


def _report(checks: Sequence[Check], groups: Optional[set[str]], console: object) -> int:
    """Run *checks*, render the report on *console*, and return the process exit code."""
    doctor = Doctor(checks)
    report = doctor.run(groups)
    doctor.render(report, console)
    return report.exit_code()


def _run_doctor(module: ModuleProvision, groups: Optional[set[str]]) -> int:
    """Run this module's checks, render the report, and return its process exit code."""
    console = module.console()
    if module.is_binary():
        return _report([python_check()] + module.extra_checks(), groups, console)
    cfg = module.load_config()
    root = module.project_root()
    try:
        found = _closure(module, root)
    except ValueError as exc:
        console.error(str(exc))
        return 1
    return _report(_checks(module, cfg, _source(module, root, found), found), groups, console)


def _run_setup(module: ModuleProvision, *, dry_run: bool, yes: bool,
               toolchains: Sequence[str], gpu: bool) -> int:
    """Provision *module*'s closure, then report readiness, and return the exit code."""
    console = module.console()
    root = module.project_root()
    cfg = module.load_config()
    try:
        found = _closure(module, root)
    except ValueError as exc:
        console.error(str(exc))
        return 1
    if found.missing:
        for name, wanted_by in found.missing:
            console.error(_missing_module_message(name, wanted_by))
        return _EXIT_USAGE
    source = _source(module, root, found)
    try:
        chosen = selection.derive(source, _present_toolchains(cfg),
                                  requested=toolchains, gpu=gpu)
    except ValueError as exc:
        console.error(str(exc))
        return _EXIT_USAGE
    managers = _managers_for(cfg)
    pipeline = InstallPipeline([
        DetectStep(source, managers),
        InstallDepsStep(source, managers),
        ConfigureStep(ModuleSink(root / "cli", _MODULE_SINK_HEADER)),
    ])
    ctx = InstallContext(
        cfg=cfg,
        selection=chosen,
        consumer=module.profile.key,
        program=module.profile.program,
        dry_run=dry_run,
        assume_acpp_llvm=yes,
    )
    try:
        with ProvisionLock(home.root() / ".lock", timeout=_LOCK_TIMEOUT):
            ok = pipeline.run(ctx, show_progress=_SHOW_PROGRESS)
    except LockTimeout as exc:
        console.error(str(exc))
        return 1
    if not ok:
        return 1
    return _run_doctor(module, None)


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
    """Add the four provision commands to *app*, or ``doctor`` alone to a binary install."""
    import typer

    def command():
        """Return the decorator that registers a command under the module's panel."""
        return app.command(rich_help_panel=module.panel)

    binary = module.is_binary()

    if not binary:
        @command()
        def setup(
            dry_run: bool = typer.Option(False, "--dry-run", help="Show, don't change."),
            yes: bool = typer.Option(
                False, "--yes", help="Assume yes on the LLVM-download prompt, for unattended runs."),
            toolchain: Optional[list[str]] = typer.Option(
                None, "--toolchain",
                help="Also install this toolchain: "
                     + " | ".join(selection.toolchain_keys()) + ". Repeatable."),
            no_gpu: bool = typer.Option(
                False, "--no-gpu", help="Skip the toolkit for this machine's GPU."),
        ) -> None:
            """Provision what this module needs to build, then report readiness."""
            bind_console(module.console)
            raise typer.Exit(_run_setup(module, dry_run=dry_run, yes=yes,
                                        toolchains=toolchain or (), gpu=not no_gpu))

    @command()
    def doctor(
        for_group: Optional[str] = typer.Option(
            None, "--for", help="Restrict the report to one check group."),
    ) -> None:
        """Report on this machine's readiness to build the module."""
        bind_console(module.console)
        if for_group is not None and for_group not in GROUPS:
            module.console().error(
                f"Unknown check group '{for_group}'; choose one of: {', '.join(GROUPS)}.")
            raise typer.Exit(2)
        groups = {for_group} if for_group else None
        raise typer.Exit(_run_doctor(module, groups))

    if binary:
        return

    @command()
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
        try:
            write_link(root / "cli", target)
        except LinkEditError as exc:
            console.error(str(exc))
            raise typer.Exit(1)
        write_module(target, module.profile.key, root)
        console.success(f"Linked {module.profile.name} into {target}.")

    @command()
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
        try:
            clear_link(root / "cli")
        except LinkEditError as exc:
            console.error(str(exc))
            raise typer.Exit(1)
        removed = [remove_module(target, name)
                   for name in dict.fromkeys((module.profile.key, module.profile.name))]
        if any(removed):
            console.success(f"Unlinked {module.profile.name} from {target}.")
        else:
            console.info(f"{module.profile.name} was not linked into {target}.")
