# key_factory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Composes the package key of a library from its source, its inputs and its toolchain."""

from __future__ import annotations

from typing import Callable

from .configure_inputs import ConfigureInputs
from .library_node import LibraryNode
from .package_key import PackageKey
from .package_request import PackageRequest
from .source_state import ISourceInspector, describe_source

#: The recipe name of the library build: tests, examples and benchmarks off.
K_RECIPE = "lean-1"


class KeyFactory:
    """Builds the key of a library for a request."""

    def __init__(self, inspector: ISourceInspector, inputs: ConfigureInputs,
                 identify: Callable[[str], str], version: str) -> None:
        """Bind the factory to the readers it composes.

        Args:
            inspector: Lists a checkout's files for the source hash.
            inputs: Reads the configure inputs.
            identify: Returns the identity of a compiler path.
            version: The SushiCore version, part of the recipe.
        """
        self._inspector = inspector
        self._inputs = inputs
        self._identify = identify
        self._recipe = f"{K_RECIPE}+sushicore-{version}"
        self._toolchains: dict[str, str] = {}

    def toolchain(self, compiler: str) -> str:
        """Return the identity of *compiler*, probed once."""
        if compiler not in self._toolchains:
            self._toolchains[compiler] = self._identify(compiler)
        return self._toolchains[compiler]

    def make(self, node: LibraryNode, request: PackageRequest,
             below: tuple[tuple[str, str], ...]) -> PackageKey:
        """Return the key of *node* for *request*, built against the packages *below*."""
        return PackageKey(
            name=node.name,
            source=describe_source(node.checkout, self._inspector, node.package_exclude),
            toolchain=self.toolchain(request.compiler),
            build_type=request.build_type.lower(),
            recipe=self._recipe,
            inputs=self._inputs.read(node.checkout, request.vcpkg_root, request.triplet),
            options=tuple(request.options.get(node.name, ())),
            below=below,
        )
