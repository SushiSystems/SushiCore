# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Merges dependency fragments from an explicit list of files."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from dataclasses import fields as dc_fields
from pathlib import Path
from typing import Iterable

from sushicore import deps_fragment
from sushicore.deps_fragment import Dependency as FragmentDependency
from sushicore.provision._output import console

#: Owner label for dependencies contributed by no single module.
SHARED_OWNER = "shared"


@dataclass(frozen=True)
class Dependency(FragmentDependency):
    """Carries a fragment's entry plus the owner that contributed it."""

    #: Which module contributed this dependency.
    owner: str = SHARED_OWNER

    def vcpkg_fallback_ports(self, platform: str) -> list[str]:
        """Return the vcpkg ports to install on Linux when this dep has no apt package."""
        if platform == "windows" or self.linux_apt:
            return []
        return self.windows_vcpkg


def _merge_ports(first: list[str], second: list[str]) -> list[str]:
    """Union two package lists, keeping one entry per port with all its features.

    Returns:
        The ports in the order first met, each carrying every feature either
        list asked for.
    """
    features: dict[str, list[str]] = {}
    for port in [*first, *second]:
        name, _, rest = port.partition("[")
        wanted = [f.strip() for f in rest.rstrip("]").split(",") if f.strip()]
        for feature in wanted:
            if feature not in features.setdefault(name, []):
                features[name].append(feature)
        features.setdefault(name, [])
    return [name + (f"[{','.join(f)}]" if f else "") for name, f in features.items()]


def _merge(existing: Dependency, incoming: Dependency) -> tuple[Dependency, str]:
    """Combine two declarations of one dependency without losing either.

    Returns:
        The merged dependency, and a warning to print when a field could not be
        merged and one had to be chosen; empty when nothing was lost.
    """
    lost = []
    for field in ("check_cmd", "provides"):
        one, two = getattr(existing, field), getattr(incoming, field)
        if one and two and one != two:
            lost.append(field)
    owner = existing.owner
    if incoming.required and not existing.required:
        owner = incoming.owner
    merged = replace(
        existing,
        owner=owner,
        description=existing.description or incoming.description,
        required=existing.required or incoming.required,
        gpu_only=existing.gpu_only and incoming.gpu_only,
        linux_apt=_merge_ports(existing.linux_apt, incoming.linux_apt),
        windows_vcpkg=_merge_ports(existing.windows_vcpkg, incoming.windows_vcpkg),
        check_cmd=existing.check_cmd or incoming.check_cmd,
        provides=existing.provides or incoming.provides,
    )
    if not lost:
        return merged, ""
    return merged, (
        f"{existing.owner} and {incoming.owner} declare '{existing.name}' with different "
        f"{' and '.join(lost)}; {existing.owner}'s is the one used.")


class IDependencySource(ABC):
    """Sources the dependency list."""

    @abstractmethod
    def all(self) -> list[Dependency]:
        """Return every declared dependency, regardless of platform."""
        raise NotImplementedError

    def depends_on(self, owner: str) -> list[str]:
        """Return the owners the given owner directly builds on; empty unless overridden."""
        return []

    def selected(self, platform: str, gpu: bool) -> list[Dependency]:
        """Return the dependencies relevant to this platform/GPU choice with packages."""
        out: list[Dependency] = []
        for dep in self.all():
            if dep.gpu_only and not gpu:
                continue
            if dep.packages_for(platform) or dep.vcpkg_fallback_ports(platform):
                out.append(dep)
        return out


def _parse_manifest(path: Path, owner: str) -> tuple[list[Dependency], list[str]]:
    """Return this fragment's dependencies and its ``[module] depends_on`` list.

    Raises:
        ValueError: The reader refused the file.
    """
    fragment = deps_fragment.read(path)
    owned = [
        Dependency(**{f.name: getattr(dep, f.name) for f in dc_fields(FragmentDependency)},
                   owner=owner)
        for dep in fragment.dependencies
    ]
    return owned, fragment.depends_on


class TomlDependencySource(IDependencySource):
    """Aggregates dependency fragments from an explicit list of ``(path, owner)`` pairs."""

    def __init__(self, sources: list[tuple[Path, str]]) -> None:
        """Store the given fragment files; nothing is read until :meth:`all`."""
        self._sources = sources
        self._depends_on: dict[str, list[str]] = {}
        self._merged: list[Dependency] | None = None

    def all(self) -> list[Dependency]:
        """Return every declared dependency, merged first-wins by name.

        Raises:
            FileNotFoundError: The source was given no files to read.
        """
        if self._merged is not None:
            return list(self._merged)
        if not self._sources:
            raise FileNotFoundError(
                "No dependency manifests found. Expected at least one "
                "(path, owner) pair in the source list.")
        merged: dict[str, Dependency] = {}
        for path, owner in self._sources:
            if not path.is_file():
                continue
            deps, depends_on = _parse_manifest(path, owner)
            if depends_on:
                self._depends_on.setdefault(owner, []).extend(depends_on)
            for dep in deps:
                if dep.name in merged:
                    merged[dep.name], warning = _merge(merged[dep.name], dep)
                    if warning:
                        console.warn(warning)
                    continue
                merged[dep.name] = dep
        self._merged = list(merged.values())
        return list(self._merged)

    def depends_on(self, owner: str) -> list[str]:
        """Return the owners the given owner directly builds on; populated by :meth:`all`."""
        return self._depends_on.get(owner, [])


def owner_order(source: IDependencySource, owners: Iterable[str]) -> list[str]:
    """Order owners: :data:`SHARED_OWNER` first, then modules in dependency order.

    Args:
        source: Reads each module's ``depends_on``; call its ``all()`` first.
        owners: The owner names to order, duplicates allowed.

    Returns:
        Every distinct owner, ordered.

    Raises:
        ValueError: The modules depend on one another in a cycle.
    """
    source.all()
    distinct = list(dict.fromkeys(owners))
    ordered = [o for o in distinct if o == SHARED_OWNER]
    pending = [o for o in distinct if o != SHARED_OWNER]
    known = set(pending)

    placed: set[str] = set()
    while pending:
        ready = next(
            (m for m in pending
             if all(u in placed for u in source.depends_on(m) if u in known)),
            None,
        )
        if ready is None:
            raise ValueError(
                "Modules depend on one another in a cycle: " + ", ".join(pending))
        pending.remove(ready)
        placed.add(ready)
        ordered.append(ready)
    return ordered
