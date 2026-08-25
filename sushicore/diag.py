"""`<prog> config` and `<prog> env`: what the CLI resolved, and under what environment.

Read-only troubleshooting. When a build picks the "wrong" compiler or a path
looks off, ``config`` answers *what* was resolved and *where each value came
from* -- default, config.toml, or an environment override -- and ``env`` answers
*which environment* cmake and ctest actually run under.

Four CLIs carried a copy of this and drifted in four ways: the program named in
the prose, the environment tokens counted as build-relevant, which resolved
directories got printed, and how the build directory was found. The first three
are things a :class:`~sushicore.profile.ModuleProfile` and the config already
know; the fourth is genuinely the caller's, so it is passed in.
"""

from __future__ import annotations

import os
import platform
from dataclasses import fields
from pathlib import Path
from typing import Callable, Mapping, Protocol

from .profile import ModuleProfile
from .workspace import merge_platform_table, read_toml


class ConfigModule(Protocol):
    """The surface a CLI's ``config`` module offers these diagnostics."""

    Config: type
    _ENV_OVERRIDES: Mapping[str, str]

    def find_project_root(self, start: Path | None = ...) -> Path: ...
    def config_dir(self, root: Path | None = ...) -> Path: ...
    def load_config(self): ...


#: Config files a module layers, in the order they are reported.
_CONFIG_FILES = ("config.toml", "config.local.toml")


class Diagnostics:
    """The ``config`` and ``env`` commands for one CLI.

    @param profile     The module's identity; supplies the sibling list and the
                       environment tokens worth showing.
    @param console     The CLI's console module.
    @param config      The CLI's config module.
    @param build_env   ``(cfg, build_dir) -> dict`` returning the environment a
                       build runs under. None when the module has no build
                       environment to snapshot, which drops the ``env`` command.
    @param build_dir   ``(root) -> Path``. Passed in rather than assumed: the
                       engine derives it from a preset and sushiruntime has a
                       separate sanitizer tree, so ``<root>/build`` is a guess
                       this module has no business making.
    """

    __slots__ = ("_profile", "_console", "_config", "_build_env", "_build_dir")

    def __init__(
        self,
        *,
        profile: ModuleProfile,
        console,
        config: ConfigModule,
        build_env: Callable[[object, Path], Mapping[str, str]] | None = None,
        build_dir: Callable[[Path], Path] = lambda root: root / "build",
    ) -> None:
        self._profile = profile
        self._console = console
        self._config = config
        self._build_env = build_env
        self._build_dir = build_dir

    def _toml_keys(self, root: Path, plat: str) -> set[str]:
        """Field names explicitly present in this module's config files."""
        cfg_dir = self._config.config_dir(root)
        keys: set[str] = set()
        for fname in _CONFIG_FILES:
            doc = read_toml(cfg_dir / fname)
            if doc:
                keys.update(merge_platform_table(doc, plat).keys())
        return keys

    def _source_of(self, field_name: str, toml_keys: set[str]) -> str:
        """Where a resolved value came from, highest-precedence answer first."""
        env_var = self._config._ENV_OVERRIDES.get(field_name)
        if env_var and env_var in os.environ:
            return f"env:{env_var}"
        return "config.toml" if field_name in toml_keys else "default"

    def _resolved_paths(self, cfg, root: Path) -> list[tuple[str, str]]:
        """The runtime-resolved paths worth reporting, as label/value pairs.

        Siblings come from the profile rather than being listed again here. The
        compiler and vcpkg lines appear only for a config that resolves them --
        sushiruntime answers those questions differently and reports them itself.
        """
        rows = [("Project root", str(root))]
        for name in self._profile.siblings:
            accessor = getattr(cfg, f"{name.removeprefix('sushi')}_dir", None)
            accessor = accessor or getattr(cfg, f"{name}_dir", None)
            if callable(accessor):
                rows.append((f"{name} dir", str(accessor(root))))
        if hasattr(cfg, "resolved_compiler"):
            rows.append(("Resolved compiler", str(cfg.resolved_compiler(root))))
        if hasattr(cfg, "resolved_vcpkg"):
            rows.append(("Resolved vcpkg", str(cfg.resolved_vcpkg(root)) or "(none)"))
        return rows

    def config_show(self) -> int:
        """Print every resolved setting with the layer it came from."""
        from rich.table import Table

        console = self._console
        console.header("Resolved Configuration")
        root = self._config.find_project_root()
        cfg = self._config.load_config()
        toml_keys = self._toml_keys(root, platform.system().lower())

        table = Table(show_header=True, header_style=console.accent)
        table.add_column("Setting")
        table.add_column("Value")
        table.add_column("Source")
        for f in fields(self._config.Config):
            table.add_row(f.name, str(getattr(cfg, f.name)),
                          self._source_of(f.name, toml_keys))
        console.console.print(table)

        rows = self._resolved_paths(cfg, root)
        width = max(len(label) for label, _ in rows)
        for label, value in rows:
            console.info(f"{label:<{width}} : {value}")

        cfg_dir = self._config.config_dir(root)
        console.info(f"{'Config dir':<{width}} : {cfg_dir}")
        for fname in _CONFIG_FILES:
            # Parentheses, not brackets: every CLI used to write "[found]" here
            # and rich parsed it as a style tag and dropped it, so the marker
            # was invisible in all four.
            mark = "found" if (cfg_dir / fname).is_file() else "absent"
            console.info(f"  {fname:<20} ({mark})")
        return 0

    def env_dump(self, show_all: bool = False, build_dir: Path | None = None) -> int:
        """Print the environment a build runs under, filtered unless *show_all*."""
        from rich.table import Table

        console = self._console
        if self._build_env is None:
            console.error(f"{self._profile.program} has no build environment to dump.")
            return 1

        console.header("Build Environment")
        root = self._config.find_project_root()
        cfg = self._config.load_config()
        env = self._build_env(cfg, build_dir or self._build_dir(root))

        tokens = self._profile.env_tokens()
        shown = {
            k: v for k, v in sorted(env.items())
            if show_all or any(tok in k.upper() for tok in tokens)
        }

        table = Table(show_header=True, header_style=console.accent)
        table.add_column("Variable")
        table.add_column("Value", overflow="fold")
        for k, v in shown.items():
            table.add_row(k, v)
        console.console.print(table)

        console.info(
            f"{len(shown)} of {len(env)} variables shown"
            + ("" if show_all else " (build-relevant; use --all for everything)")
        )
        return 0
