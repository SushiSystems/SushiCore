# package_resolver.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Chooses, bottom-up, one built package for each Sushi library a consumer's chain links."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from ..closure import DEFAULT_FRAGMENT
from .build_tree import BuildTree
from .closure_walk import ClosureWalk
from .forced_packages import ForcedPackages
from .key_factory import KeyFactory
from .library_node import LibraryNode
from .link_publisher import LinkPublisher
from .package import Package
from .package_builder import BuildRequest, IPackageBuilder
from .package_choices import PackageChoices
from .package_environment import package_variable
from .package_error import PackageError
from .package_key import PackageKey
from .package_locks import PackageLocks
from .package_request import PackageRequest
from .package_set import PackageSet, ResolvedPackage
from .package_store import PackageStore

#: The owner recorded for a package chosen from the source tree.
K_SOURCE_OWNER = "the source tree"


@dataclass
class _Resolution:
    """The state of one call to :meth:`PackageResolver.resolve`."""

    request: PackageRequest
    by_name: dict[str, LibraryNode]
    choices: PackageChoices = field(default_factory=PackageChoices)
    resolved: dict[str, ResolvedPackage] = field(default_factory=dict)


class PackageResolver:
    """Resolves a consumer's chain bottom-up and refuses a library at two keys."""

    def __init__(self, walk: ClosureWalk, keys: KeyFactory, store: PackageStore,
                 builder: IPackageBuilder, forced: ForcedPackages, locks: PackageLocks,
                 publisher: LinkPublisher, report: Callable[[str], None],
                 clock: Callable[[], float] = time.monotonic) -> None:
        """Bind the resolver to its collaborators.

        Args:
            walk: Lists the libraries of the chain, dependencies first.
            keys: Composes the key of a library.
            store: Where built packages live.
            builder: Builds a package that the store lacks.
            forced: Reads the packages a parent handed down.
            locks: Hands out the checkout and key locks.
            publisher: Points the consumer's link at the chosen package.
            report: Receives one line per library.
            clock: Seconds, monotonic; replaced in tests.
        """
        self._walk = walk
        self._keys = keys
        self._store = store
        self._builder = builder
        self._forced = forced
        self._locks = locks
        self._publisher = publisher
        self._report = report
        self._clock = clock

    def resolve(self, request: PackageRequest) -> PackageSet:
        """Return the package of every library the consumer's chain links, dependencies first.

        Raises:
            PackageError: A library has no checkout, no CLI to build it, fails to build, or
                was built with another compiler.
            PackageConflictError: One library would appear at two keys.
        """
        walked = self._walk.walk(request)
        nodes = self._select(walked, request)
        left_out = tuple(node.name for node in walked if node not in nodes)
        state = _Resolution(request, {node.name: node for node in nodes})
        forced = self._forced.read([node.name for node in nodes],
                                   self._keys.toolchain(request.compiler),
                                   request.build_type.lower())
        for node in nodes:
            if node.name in forced:
                item = self._take_forced(node, forced[node.name], state)
            else:
                item = self._obtain(node, state)
            state.resolved[node.name] = item
            self._report(item.line())
        return PackageSet(tuple(state.resolved.values()), left_out)

    @staticmethod
    def _select(nodes: list[LibraryNode], request: PackageRequest) -> list[LibraryNode]:
        """Return the nodes *request* names and what they depend on, in the order of *nodes*.

        Raises:
            PackageError: A requested library is not in the closure.
        """
        if request.libraries is None:
            return nodes
        by_name = {node.name: node for node in nodes}
        for name in request.libraries:
            if name not in by_name:
                raise PackageError(
                    f"{name} is not in the closure of {request.owner}, which is "
                    f"{', '.join(by_name) or 'empty'}.")
        wanted: set[str] = set()
        pending = list(request.libraries)
        while pending:
            name = pending.pop()
            if name not in wanted:
                wanted.add(name)
                pending.extend(by_name[name].depends_on)
        return [node for node in nodes if node.name in wanted]

    def _take_forced(self, node: LibraryNode, package: Package,
                     state: _Resolution) -> ResolvedPackage:
        """Choose the package a parent handed down, with the packages it was built against."""
        state.choices.add(node.name, package.digest, package_variable(node.name))
        for below_name, below_digest in package.below():
            state.choices.add(below_name, below_digest, f"the {node.name} package")
        self._store.touch(package)
        return ResolvedPackage(package, None, built=False)

    def _obtain(self, node: LibraryNode, state: _Resolution) -> ResolvedPackage:
        """Reuse the package of *node*'s key, or build it, and publish the consumer's link."""
        below = tuple((name, state.resolved[name].package.digest) for name in node.depends_on)
        key = self._keys.make(node, state.request, below)
        state.choices.add(node.name, key.digest(), K_SOURCE_OWNER)
        package = self._store.find(key)
        built, seconds = False, 0.0
        if package is None:
            package, built, seconds = self._build(node, key, state)
        else:
            self._store.touch(package)
        tree = BuildTree(key.build_type, key.options, key.toolchain)
        link = self._publisher.publish(package, tree.id, state.request.owner)
        return ResolvedPackage(package, key, built, seconds, link)

    def _build(self, node: LibraryNode, key: PackageKey,
               state: _Resolution) -> tuple[Package, bool, float]:
        """Build the package of *key* under the checkout and key locks.

        Returns:
            The package, whether this call built it, and the seconds the build took. A package
            another process installed while this one waited for the lock is reused.

        Raises:
            PackageError: The library names no CLI, or its build fails.
        """
        if not node.cli:
            raise PackageError(
                f"{node.name} has no package {key.short()} in the store and its fragment names "
                f"no CLI to build one; add `cli = \"<command>\"` to the [module] table of "
                f"{node.checkout / DEFAULT_FRAGMENT}.")
        with self._locks.checkout(node.name, node.checkout):
            with self._locks.key(node.name, key.digest()):
                existing = self._store.find(key)
                if existing is not None:
                    self._store.touch(existing)
                    return existing, False, 0.0
                package, seconds = self._install(node, key, state)
            self._store.prune(node.name, {key.digest()} | self._publisher.protected(node.name))
        return package, True, seconds

    def _install(self, node: LibraryNode, key: PackageKey,
                 state: _Resolution) -> tuple[Package, float]:
        """Stage, build and commit the package of *key*; the caller holds both locks."""
        prefix = self._store.stage(key)
        below = {name: state.resolved[name].package.prefix
                 for name in self._below_names(node, state)}
        started = self._clock()
        try:
            self._builder.build(BuildRequest(key, node.checkout, node.cli, prefix,
                                             state.request.compiler, below))
            seconds = self._clock() - started
            return self._store.commit(key, seconds), seconds
        except PackageError:
            self._store.discard(key)
            raise

    @staticmethod
    def _below_names(node: LibraryNode, state: _Resolution) -> list[str]:
        """Return the names of every library below *node*, transitive ones included."""
        found: list[str] = []
        pending = list(node.depends_on)
        while pending:
            name = pending.pop(0)
            if name not in found:
                found.append(name)
                pending.extend(state.by_name[name].depends_on)
        return found
