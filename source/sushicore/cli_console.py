# cli_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Builds a CLI's console on first use instead of on import.

The reasoning is in docs/architecture/OVERVIEW.md, section `cli_console`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

_ATTRS = frozenset({
    "console",
    "info", "success", "warn", "error",
    "command", "header", "fail_panel", "accent",
    "table", "progress", "result", "prompt",
    "is_machine",
})


class LazyConsole:
    """Builds a :class:`~sushicore.console.Console` on first attribute access.

    *config_dir* is the CLI's own resolver for its ``cli/`` directory. It is
    called -- not read -- on first use, and is allowed to raise ``SystemExit``:
    that is how every CLI's ``config_dir`` reports "not inside a checkout", and
    it degrades here to a console with no config sources rather than killing a
    command that never needed a project.

    *machine* selects the JSON renderer. It is read once, at the first build,
    so a CLI sets it while parsing its command line, before anything prints.

    *extra_sources* returns config files that are not in that directory, such as a
    workspace's ``workspace.toml``. They sit below the directory's own files, so a
    module's setting wins over the workspace's.
    """

    __slots__ = ("_config_dir", "_console", "_extra_sources", "machine")

    def __init__(self, config_dir: Callable[[], Path],
                 extra_sources: Callable[[], Sequence[Path]] | None = None) -> None:
        """Remember the config-dir resolver and any extra files; nothing is built yet."""
        self._config_dir = config_dir
        self._extra_sources = extra_sources
        self._console = None
        self.machine = False

    @property
    def built(self) -> bool:
        """Whether the console has been materialised yet. For tests."""
        return self._console is not None

    def sources(self) -> Sequence[Path]:
        """The config files to layer, lowest precedence first; the extra files only outside a checkout."""
        extra = list(self._extra_sources()) if self._extra_sources is not None else []
        try:
            cfg_dir = self._config_dir()
        except SystemExit:
            return extra
        return [*extra, cfg_dir / "config.toml", cfg_dir / "config.local.toml"]

    def get(self):
        """Return the console, building it once on first call."""
        if self._console is None:
            from . import build_console

            self._console = build_console(self.sources(), machine=self.machine)
        return self._console

    def attribute(self, name: str):
        """Resolve *name* against the console. Wire as a module ``__getattr__``."""
        if name in _ATTRS:
            console = self.get()
            return console.console if name == "console" else getattr(console, name)
        raise AttributeError(f"no console attribute {name!r}")
