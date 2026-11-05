# diag_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""A CLI config module held in memory, for the diagnostics that read one."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence


class InMemoryConfigModule:
    """Offers a fixed project root, config directory, config values and config file list.

    No file is read or written; the paths are only names.

    Args:
        root: The project root ``find_project_root`` returns.
        config_cls: The settings class, a dataclass.
        values: The field values ``load_config`` builds the settings from.
        env_overrides: The environment variable that overrides each field.
        config_dir: The config directory; ``<root>/cli`` when not given.
        sources: The config files, lowest precedence first; the directory's
            ``config.toml`` and ``config.local.toml`` when not given.
    """

    def __init__(self, root: Path, config_cls: type, values: Mapping[str, object] | None = None,
                 *, env_overrides: Mapping[str, str] | None = None,
                 config_dir: Path | None = None, sources: Sequence[Path] | None = None) -> None:
        """Hold the root, the settings class and the values."""
        self.Config = config_cls
        self._ENV_OVERRIDES = dict(env_overrides or {})
        self._root = root
        self._values = dict(values or {})
        self._config_dir = config_dir if config_dir is not None else root / "cli"
        self._sources = list(sources) if sources is not None else None

    def find_project_root(self, start: Path | None = None) -> Path:
        """Return the project root, wherever the search would start."""
        return self._root

    def config_dir(self, root: Path | None = None) -> Path:
        """Return the config directory."""
        return self._config_dir

    def load_config(self):
        """Return a settings object built from the values."""
        return self.Config(**self._values)

    def sources(self) -> list[Path]:
        """Return the config files, lowest precedence first."""
        if self._sources is not None:
            return list(self._sources)
        return [self._config_dir / "config.toml", self._config_dir / "config.local.toml"]
