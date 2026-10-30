# link_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Links a module into a workspace, and unlinks it."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..errors import SushiCoreError
from ..workspace import (
    WORKSPACE_MARKER,
    clear_link,
    has_marker,
    read_link,
    remove_module,
    resolve_env_path,
    walk_up,
    write_link,
    write_module,
)
from .module_provision import ModuleProvision
from .outcome import K_EXIT_USAGE, Outcome, done, failed


def _resolve_workspace(explicit: Optional[Path], project_root: Path) -> Optional[Path]:
    """Returns the workspace root: ``--workspace``, then ``SUSHISTACK_HOME``, then a walk-up."""
    if explicit is not None:
        return explicit
    env = resolve_env_path("SUSHISTACK_HOME")
    if env is not None:
        return env
    return walk_up(project_root, has_marker(WORKSPACE_MARKER))


def _no_workspace_message() -> str:
    """Returns the error shown when no workspace can be resolved."""
    return (
        "No workspace found: pass --workspace, set SUSHISTACK_HOME, or run inside a "
        f"directory with a {WORKSPACE_MARKER} ancestor."
    )


def _restore_link(config_dir: Path, previous: Path | None) -> None:
    """Puts the workspace link in *config_dir* back to what it was before a failed link."""
    if previous is None:
        clear_link(config_dir)
    else:
        write_link(config_dir, previous)


def run_link(module: ModuleProvision, workspace: Optional[Path]) -> Outcome:
    """Records this module's location in a workspace's registry, as one operation.

    The workspace must carry its marker. The link in the module and the registry entry are written
    together: when the second write fails the first is put back.
    """
    console = module.console()
    root = module.project_root()
    target = _resolve_workspace(workspace, root)
    if target is None:
        console.error(_no_workspace_message())
        return failed(K_EXIT_USAGE)
    if not has_marker(WORKSPACE_MARKER)(target):
        console.error(f"{target} is not a workspace: it has no {WORKSPACE_MARKER}.")
        return failed(K_EXIT_USAGE)
    config_dir = root / module.config_dir
    try:
        previous = read_link(config_dir)
        write_link(config_dir, target)
    except SushiCoreError as exc:
        console.error(str(exc))
        return failed()
    try:
        write_module(target, module.profile.key, root)
    except (OSError, SushiCoreError) as exc:
        _restore_link(config_dir, previous)
        console.error(f"Could not register {module.profile.name} in {target}: {exc}")
        return failed()
    console.success(f"Linked {module.profile.name} into {target}.")
    return done()


def run_unlink(module: ModuleProvision, workspace: Optional[Path]) -> Outcome:
    """Removes this module's entry from a workspace's registry and its link."""
    console = module.console()
    root = module.project_root()
    target = _resolve_workspace(workspace, root)
    if target is None:
        console.error(_no_workspace_message())
        return failed(K_EXIT_USAGE)
    try:
        clear_link(root / module.config_dir)
    except SushiCoreError as exc:
        console.error(str(exc))
        return failed()
    removed = [remove_module(target, name)
               for name in dict.fromkeys((module.profile.key, module.profile.name))]
    if any(removed):
        console.success(f"Unlinked {module.profile.name} from {target}.")
    else:
        console.info(f"{module.profile.name} was not linked into {target}.")
    return done()
