# closure_walk.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Lists the libraries of a consumer's chain, each after the libraries it depends on."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from ... import deps_fragment
from ..closure import DEFAULT_FRAGMENT
from .library_node import LibraryNode
from .package_error import PackageError
from .package_request import PackageRequest
from .source_locator import ISourceLocator

#: Reads the fragment at a path; one that is absent declares nothing.
ReadFragment = Callable[[Path], "deps_fragment.Fragment | None"]


class ClosureWalk:
    """Follows ``depends_on`` through the fragments of the libraries."""

    def __init__(self, locator: ISourceLocator,
                 read_fragment: ReadFragment = deps_fragment.read_present) -> None:
        """Bind the walk to what finds checkouts and reads fragments.

        Args:
            locator: Finds a library's checkout.
            read_fragment: Reads a fragment; replaced in tests.
        """
        self._locator = locator
        self._read = read_fragment

    def walk(self, request: PackageRequest) -> list[LibraryNode]:
        """Return the libraries the consumer's chain links, dependencies first, each once.

        The version a pin names is the first one found, the consumer's before any library's.

        Raises:
            PackageError: A fragment is malformed, a checkout is missing, or the libraries
                depend on one another in a cycle.
        """
        fragment = self._fragment(request.root / request.fragment)
        versions: dict[str, str] = {}
        self._pin(versions, fragment)
        done: dict[str, LibraryNode] = {}
        for name in fragment.depends_on:
            self._visit(name, (request.owner,), request, versions, done)
        return list(done.values())

    def _visit(self, name: str, trail: tuple[str, ...], request: PackageRequest,
               versions: dict[str, str], done: dict[str, LibraryNode]) -> None:
        """Add *name* to *done* after the libraries it depends on."""
        if name in trail:
            raise PackageError(
                "Modules depend on one another in a cycle: " + " -> ".join((*trail, name)))
        if name in done:
            return
        checkout = self._locator.locate(request.root, name, versions.get(name, ""),
                                        request.configured.get(name, ""))
        fragment = self._fragment(checkout / DEFAULT_FRAGMENT)
        self._pin(versions, fragment)
        for dependency in fragment.depends_on:
            self._visit(dependency, (*trail, name), request, versions, done)
        done[name] = LibraryNode(name, checkout, fragment.cli, tuple(fragment.package_exclude),
                                 tuple(fragment.depends_on))

    def _fragment(self, path: Path) -> deps_fragment.Fragment:
        """Read the fragment at *path*; an absent one is empty."""
        try:
            return self._read(path) or deps_fragment.Fragment([], [])
        except ValueError as exc:
            raise PackageError(str(exc)) from exc

    @staticmethod
    def _pin(versions: dict[str, str], fragment: deps_fragment.Fragment) -> None:
        """Remember the version each pin of *fragment* names, the first pin of a library first."""
        for pin in fragment.pins:
            versions.setdefault(pin.name, pin.version)
