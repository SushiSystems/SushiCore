"""Layered appearance config: resolves *what* theme/icons/color-mode to use.

Deliberately knows nothing about *how* a repo finds its own config directory
— that discovery (walking up for a marker file, etc.) is repo-specific and
stays in each CLI. This module only merges a list of TOML files the caller
hands it, highest-precedence last, plus environment variables on top. That
keeps one seam: every Sushi* CLI points this loader at its own
``config.toml`` / ``config.local.toml`` and gets the same merge behavior.

Schema (in any of the given TOML files)::

    [cli]
    theme = "default"      # preset name; see sushicore.theme
    icons = "text"         # preset name; see sushicore.icons
    color = "auto"         # auto | always | never
    background = "auto"    # auto | dark | light

    [cli.colors]           # optional partial override merged onto the preset
    error = "bold red on white"

    [cli.icon_overrides]   # optional partial override merged onto the icon preset
    warn = "!!"

    [cli.windows]          # optional platform-specific override (any of the
    icons = "text"         # above keys), merged over the common [cli] table
"""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field
from pathlib import Path

from .terminal_background import K_AUTO, K_VALUES

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.10 fallback
    import tomli as tomllib

_ENV_PREFIX = "SUSHI_CLI"


@dataclass
class AppearanceSpec:
    theme: str = "default"
    icons: str = "text"
    color: str = "auto"  # auto | always | never
    background: str = "auto"  # auto | dark | light
    color_overrides: dict = field(default_factory=dict)
    icon_overrides: dict = field(default_factory=dict)


def _read_toml(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open("rb") as fh:
        return tomllib.load(fh)


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


def load_appearance(config_paths: list[Path]) -> AppearanceSpec:
    """Merge ``config_paths`` (low -> high precedence) and environment overrides."""
    plat = platform.system().lower()  # 'windows' | 'linux' | 'darwin'
    spec = AppearanceSpec()

    for path in config_paths:
        doc = _read_toml(path)
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

    env = os.environ
    if f"{_ENV_PREFIX}_THEME" in env:
        spec.theme = env[f"{_ENV_PREFIX}_THEME"]
    if f"{_ENV_PREFIX}_ICONS" in env:
        spec.icons = env[f"{_ENV_PREFIX}_ICONS"]
    if f"{_ENV_PREFIX}_COLOR" in env:
        spec.color = env[f"{_ENV_PREFIX}_COLOR"]
    if f"{_ENV_PREFIX}_BACKGROUND" in env:
        spec.background = env[f"{_ENV_PREFIX}_BACKGROUND"]
    if "NO_COLOR" in env:  # https://no-color.org — always wins when set
        spec.color = "never"

    if spec.color not in ("auto", "always", "never"):
        spec.color = "auto"
    if spec.background not in K_VALUES:
        spec.background = K_AUTO

    return spec
