# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The registry of components installed under the dependency root."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.10 fallback
    import tomli as tomllib

from . import home

_HEADER = "# Components installed under this dependency root. Written by sushicore.provision.\n"


@dataclass(frozen=True)
class Component:
    """One installed component and the consumers that depend on it.

    Args:
        name: The component's name, e.g. ``"intel-llvm"``.
        version: The installed version string.
        path: Absolute path to the installed component on disk.
        source: Where the component came from, e.g. a repository slug.
        installed_at: ISO-8601 UTC timestamp of the install.
        consumers: Names of the modules currently depending on this install.
    """

    name: str
    version: str
    path: str
    source: str
    installed_at: str
    consumers: tuple[str, ...]


class RegistryError(Exception):
    """Raised when the registry file exists but cannot be parsed."""


def default_path() -> Path:
    """Return ``home.root() / "registry.toml"``."""
    return home.root() / "registry.toml"


class Registry:
    """Tracks components installed under a dependency root, backed by a TOML file."""

    def __init__(self, path: Path) -> None:
        """Bind the registry to *path*; call :meth:`load` before reading it.

        Args:
            path: The ``registry.toml`` file this registry reads and writes.
        """
        self._path = path
        self._components: dict[tuple[str, str], Component] = {}

    def load(self) -> None:
        """Read the registry file, or start empty when it does not exist.

        Raises:
            RegistryError: The file exists but is not valid TOML.
        """
        self._components = {}
        if not self._path.is_file():
            return
        try:
            with self._path.open("rb") as fh:
                doc = tomllib.load(fh)
        except tomllib.TOMLDecodeError as exc:
            raise RegistryError(f"{self._path}: {exc}") from exc
        for entry in doc.get("component", []):
            component = Component(
                name=entry["name"],
                version=entry["version"],
                path=entry["path"],
                source=entry["source"],
                installed_at=entry["installed_at"],
                consumers=tuple(entry.get("consumers", ())),
            )
            self._components[(component.name, component.version)] = component

    def components(self) -> list[Component]:
        """Return every registered component."""
        return list(self._components.values())

    def find(self, name: str, version: str | None = None) -> Component | None:
        """Return the component matching *name* (and *version* when given).

        Args:
            name: The component name to look up.
            version: When given, only a component at this exact version matches;
                otherwise the first registered version for *name* matches.
        """
        if version is not None:
            return self._components.get((name, version))
        for component in self._components.values():
            if component.name == name:
                return component
        return None

    def add(self, component: Component) -> None:
        """Register *component*, merging its consumers into an existing entry.

        Args:
            component: The component to add. When a component with the same
                name and version is already registered, the two consumer sets
                are merged rather than duplicated.
        """
        key = (component.name, component.version)
        existing = self._components.get(key)
        if existing is None:
            self._components[key] = component
            return
        merged_consumers = tuple(
            dict.fromkeys((*existing.consumers, *component.consumers)))
        self._components[key] = Component(
            name=component.name,
            version=component.version,
            path=component.path,
            source=component.source,
            installed_at=component.installed_at,
            consumers=merged_consumers,
        )

    def release(self, name: str, version: str, consumer: str) -> bool:
        """Remove *consumer* from a component's consumer list.

        Args:
            name: The component name.
            version: The component version.
            consumer: The consumer to drop.

        Returns:
            ``True`` when the component has no consumer left after the removal,
            ``False`` otherwise (including when the component is unregistered).
        """
        key = (name, version)
        existing = self._components.get(key)
        if existing is None:
            return False
        remaining = tuple(c for c in existing.consumers if c != consumer)
        self._components[key] = Component(
            name=existing.name,
            version=existing.version,
            path=existing.path,
            source=existing.source,
            installed_at=existing.installed_at,
            consumers=remaining,
        )
        return len(remaining) == 0

    def save(self) -> None:
        """Write the registry to its file, replacing it atomically."""
        lines = [_HEADER]
        for component in self._components.values():
            lines.append("\n[[component]]\n")
            lines.append(f"name = {json.dumps(component.name)}\n")
            lines.append(f"version = {json.dumps(component.version)}\n")
            lines.append(f"path = {json.dumps(component.path)}\n")
            lines.append(f"source = {json.dumps(component.source)}\n")
            lines.append(f"installed_at = {json.dumps(component.installed_at)}\n")
            consumers = "[" + ", ".join(json.dumps(c) for c in component.consumers) + "]"
            lines.append(f"consumers = {consumers}\n")
        tmp_path = self._path.with_suffix(".toml.tmp")
        tmp_path.write_text("".join(lines), encoding="utf-8")
        os.replace(tmp_path, self._path)
