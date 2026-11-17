# config.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Resolves the theme, icon set and colour mode from TOML files and the environment.

The reasoning is in docs/architecture/OVERVIEW.md, section `config`.
The schema of the `[cli]` table is in docs/reference/CONFIGURATION.md.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import final

from .environment import Environment, ProcessEnvironment
from .files import Files
from .icon_registry import IconRegistry
from .icons import DEFAULT_ICON_REGISTRY
from .terminal_background import K_AUTO, K_VALUES
from .theme import DEFAULT_THEME_REGISTRY
from .theme_registry import ThemeRegistry
from .layered_toml import read_toml

_ENV_PREFIX = "SUSHI_CLI"


@final
@dataclass(slots=True)
class AppearanceSpec:
    """Names the theme, the icon set and the platform a console is drawn for."""
    theme: str = "default"
    icons: str = "text"
    color: str = "auto"  # auto | always | never
    background: str = "auto"  # auto | dark | light
    color_overrides: dict = field(default_factory=dict)
    icon_overrides: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)


_OVERRIDE_TABLES = ("colors", "icon_overrides")


def _merge_cli_table(doc: dict, plat: str) -> dict:
    """Merge common ``[cli]`` with ``[cli.<platform>]`` (platform wins)."""
    cli = dict(doc.get("cli", {}))
    merged = {k: v for k, v in cli.items() if not isinstance(v, dict) or k in _OVERRIDE_TABLES}
    plat_table = cli.get(plat, {})
    if isinstance(plat_table, dict):
        merged.update({k: v for k, v in plat_table.items() if not isinstance(v, dict)})
        for table_name in _OVERRIDE_TABLES:
            if isinstance(plat_table.get(table_name), dict):
                merged[table_name] = {**merged.get(table_name, {}), **plat_table[table_name]}
    return merged


def load_appearance(config_paths: list[Path], *, environment: Environment | None = None,
                    files: Files | None = None, theme_registry: ThemeRegistry | None = None,
                    icon_registry: IconRegistry | None = None) -> AppearanceSpec:
    """Merge ``config_paths`` (low -> high precedence) and environment overrides.

    @param environment The variables read for the overrides; the process environment when None.
    @param files       The file system the config files are read through; the disk when None.
    @param theme_registry The themes a name may select; the default registry when None.
    @param icon_registry  The icon sets a name may select; the default registry when None.
    @throws ConfigError When a config file is not valid TOML.
    """
    plat = platform.system().lower()  # 'windows' | 'linux' | 'darwin'
    spec = AppearanceSpec()

    for path in config_paths:
        doc = read_toml(path, files=files)
        if not doc:
            continue
        table = _merge_cli_table(doc, plat)
        if "theme" in table and isinstance(table["theme"], str):
            spec.theme = table["theme"]
        if "icons" in table and isinstance(table["icons"], str):
            spec.icons = table["icons"]
        if "color" in table and isinstance(table["color"], str):
            spec.color = table["color"]
        if "background" in table and isinstance(table["background"], str):
            spec.background = table["background"]
        colors = table.get("colors")
        if isinstance(colors, dict):
            spec.color_overrides.update(colors)
        icon_overrides = table.get("icon_overrides")
        if isinstance(icon_overrides, dict):
            spec.icon_overrides.update(icon_overrides)

    env = ProcessEnvironment() if environment is None else environment
    for name in ("theme", "icons", "color", "background"):
        variable = f"{_ENV_PREFIX}_{name.upper()}"
        if env.has(variable):
            setattr(spec, name, env.get(variable, ""))
    if env.has("NO_COLOR"):  # https://no-color.org — always wins when set
        spec.color = "never"

    _settle(spec, "theme", (theme_registry or DEFAULT_THEME_REGISTRY).known(), "default")
    _settle(spec, "icons", (icon_registry or DEFAULT_ICON_REGISTRY).known(), "text")
    _settle(spec, "color", ("auto", "always", "never"), "auto")
    _settle(spec, "background", K_VALUES, K_AUTO)
    return spec


def _settle(spec: AppearanceSpec, name: str, allowed: tuple[str, ...], default: str) -> None:
    """Replace an unknown value of *name* by *default*, and record one warning that says so.

    One policy covers every appearance setting: a wrong value never stops a command, and it is never
    ignored in silence.
    """
    value = getattr(spec, name)
    if value in allowed:
        return
    spec.warnings.append(
        f"Unknown CLI {name} '{value}'; using '{default}'. Known: {', '.join(sorted(allowed))}.")
    setattr(spec, name, default)
