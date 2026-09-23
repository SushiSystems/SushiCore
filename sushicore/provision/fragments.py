# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Aggregating dependency fragments from an explicit list of files.

The installer must not hard-code package names. Instead it asks an
``IDependencySource`` for the packages relevant to the current platform.

SushiStack owns no single manifest. Each module declares what it needs, and a
caller aggregates those fragments into one shared dependency set. Which files
make up that set is the caller's business (workspace discovery, a shipped
``manifests/`` directory, a fixed test list); this module only merges the
files it is given.

When two fragments declare the same dependency name the first one wins and a
warning is emitted, so the union stays predictable. Tests can inject an
in-memory source.
"""

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
    """A fragment's entry plus the module that contributed it.

    The fields and their meaning are :mod:`sushicore.deps_fragment`'s, read once
    for every CLI that reads this format. What this adds is ownership, which is
    the caller's business rather than the file's: a fragment says what it
    needs, not who is asking.
    """

    #: Which module contributed this dependency.
    owner: str = SHARED_OWNER

    def vcpkg_fallback_ports(self, platform: str) -> list[str]:
        """Vcpkg ports to install on Linux when this dep has no apt package.

        vcpkg port names are the same cross-platform, so ``windows_vcpkg`` also
        names the Linux ports for a library that ships no apt package at all
        (``linux_apt = []`` in the manifest, e.g. vk-bootstrap, cgltf) — without
        this, such a dependency is silently unprovisionable on Linux. Empty
        on Windows (windows_vcpkg is already the primary path there) and empty
        whenever an apt package exists (apt is the native, preferred route).
        """
        if platform == "windows" or self.linux_apt:
            return []
        return self.windows_vcpkg


def _merge_ports(first: list[str], second: list[str]) -> list[str]:
    """Union two package lists, keeping one entry per port with all its features.

    A vcpkg port carries its feature set in brackets, so ``sdl2`` and
    ``sdl2[vulkan]`` name one port at two strengths. Taking either alone would
    drop a feature a module needs; the union keeps both.

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

    Modules declare what they need, not what the workspace installs, so two
    modules naming the same dependency differently are both right. The merge
    takes the stronger of every field: required if either requires it, every
    package either asks for, and GPU-only only when both say so. Ownership goes
    to the first module that required it, because that is the module whose
    absence would make the dependency unnecessary.

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
    """Source of the dependency list. Abstraction the steps depend on."""

    @abstractmethod
    def all(self) -> list[Dependency]:
        """Every declared dependency, regardless of platform."""
        raise NotImplementedError

    def depends_on(self, owner: str) -> list[str]:
        """Modules the given owner directly builds on. Empty unless overridden."""
        return []

    def selected(self, platform: str, gpu: bool) -> list[Dependency]:
        """Dependencies relevant to this platform/GPU choice with packages.

        Filters out gpu-only entries when ``gpu`` is False and entries that
        declare no package for this platform — including no apt package *and*
        no vcpkg fallback (see :meth:`Dependency.vcpkg_fallback_ports`).
        """
        out: list[Dependency] = []
        for dep in self.all():
            if dep.gpu_only and not gpu:
                continue
            if dep.packages_for(platform) or dep.vcpkg_fallback_ports(platform):
                out.append(dep)
        return out


def _parse_manifest(path: Path, owner: str) -> tuple[list[Dependency], list[str]]:
    """Return this fragment's dependencies and its ``[module] depends_on`` list.

    The file is read by :mod:`sushicore.deps_fragment`, the one reader of this
    format; all this adds is the owner, which the file does not carry and the
    caller needs.

    Raises:
        ValueError: The reader refused the file. A shape it does not understand
            is a defect to report: skipping one is how sushidsp's whole fragment
            went unread until 2026-09-22.
    """
    fragment = deps_fragment.read(path)
    owned = [
        Dependency(**{f.name: getattr(dep, f.name) for f in dc_fields(FragmentDependency)},
                   owner=owner)
        for dep in fragment.dependencies
    ]
    return owned, fragment.depends_on


class TomlDependencySource(IDependencySource):
    """Aggregates dependency fragments from an explicit list of files.

    ``sources`` is ``(path, owner)`` pairs, given by the caller — which files
    make up the workspace's fragment set is the caller's business, not this
    class's. The union is read with first-wins de-duplication by name.
    Alongside the merged dependencies it records, per owning module, which
    modules that module ``depends_on`` — so callers can reason about a
    module's *effective* dependency set (its own plus those it builds on).
    """

    def __init__(self, sources: list[tuple[Path, str]]) -> None:
        """Store the given fragment files; nothing is read until :meth:`all`."""
        self._sources = sources
        self._depends_on: dict[str, list[str]] = {}
        self._merged: list[Dependency] | None = None

    def all(self) -> list[Dependency]:
        """Return every declared dependency, merged first-wins by name.

        Read once and kept: several steps of one run ask for the set, the files
        do not change under them, and a duplicate would otherwise be reported
        again for each asking.

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
        """Modules the given owner directly builds on (``[module] depends_on``).

        Populated as a side effect of :meth:`all`; call ``all()`` first (the
        readiness reporter does).
        """
        return self._depends_on.get(owner, [])


def owner_order(source: IDependencySource, owners: Iterable[str]) -> list[str]:
    """Order owners: :data:`SHARED_OWNER` first, then modules in dependency order.

    Ties keep the input order. A ``depends_on`` entry naming an owner outside
    *owners* is ignored, so a partially cloned workspace still orders.

    Args:
        source: Reads each module's ``depends_on``; its ``all()`` is called
            first because the TOML source fills that map there.
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
