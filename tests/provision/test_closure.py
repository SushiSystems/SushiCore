# test_closure.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the dependency closure."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.deps_fragment import Fragment
from sushicore.provision.closure import DEFAULT_FRAGMENT, resolve


class _Checkouts:
    """Module checkouts held as values: each module's dependencies, or None for a bare folder."""

    def __init__(self, modules: dict[str, list[str] | None]) -> None:
        """Place each module under a made-up root and give those with dependencies a fragment."""
        self._roots = {name: Path("/machine") / name for name in modules}
        self._fragments = {
            self._roots[name] / DEFAULT_FRAGMENT: Fragment([], depends_on=list(deps))
            for name, deps in modules.items() if deps is not None}

    def root(self, name: str) -> Path:
        """Return the checkout of *name*."""
        return self._roots[name]

    def locate(self, name: str) -> Path | None:
        """Return the checkout of *name*, or None when there is none."""
        return self._roots.get(name)

    def is_file(self, path: Path) -> bool:
        """Report whether *path* holds a fragment."""
        return path in self._fragments

    def read(self, path: Path) -> Fragment:
        """Return the fragment at *path*."""
        return self._fragments[path]

    def resolve(self, key: str, **options):
        """Resolve *key* over these checkouts."""
        return resolve(key, self.root(key), self.locate, is_file=self.is_file, read=self.read,
                       **options)


def _owners(closure) -> list[str]:
    """Return the owner of each source of *closure*, in order."""
    return [owner for _path, owner in closure.sources]


@pytest.mark.small
def test_a_module_with_no_dependencies_is_its_own_closure():
    """Check that a module with no dependencies is its own closure."""
    checkouts = _Checkouts({"sushiruntime": []})
    closure = checkouts.resolve("sushiruntime")
    assert closure.sources == ((checkouts.root("sushiruntime") / DEFAULT_FRAGMENT, "sushiruntime"),)
    assert closure.missing == ()


@pytest.mark.small
def test_a_chain_is_ordered_dependencies_first():
    """Check that a chain is ordered dependencies first."""
    checkouts = _Checkouts({"sushiruntime": [], "sushiblas": ["sushiruntime"],
                            "sushiai": ["sushiruntime", "sushiblas"]})
    assert _owners(checkouts.resolve("sushiai")) == ["sushiruntime", "sushiblas", "sushiai"]


@pytest.mark.small
def test_shared_fragments_come_first():
    """Check that shared fragments come first."""
    base = Path("/machine/base.deps.toml")
    closure = _Checkouts({"sushiruntime": []}).resolve("sushiruntime", shared=[(base, "shared")])
    assert closure.sources[0] == (base, "shared")


@pytest.mark.small
def test_a_missing_checkout_is_reported_with_who_wanted_it():
    """Check that a missing checkout is reported with who wanted it."""
    closure = _Checkouts({"sushiblas": ["sushiruntime"]}).resolve("sushiblas")
    assert closure.missing == (("sushiruntime", "sushiblas"),)


@pytest.mark.small
def test_a_missing_checkout_leaves_the_module_that_wanted_it_in_the_closure():
    """Check that the module that wanted a missing checkout is still a source."""
    closure = _Checkouts({"sushiblas": ["sushiruntime"]}).resolve("sushiblas")
    assert _owners(closure) == ["sushiblas"]


@pytest.mark.small
def test_a_missing_middle_module_hides_nothing_above_it():
    """Check that a missing middle module hides nothing above it."""
    checkouts = _Checkouts({"sushiruntime": [], "sushiai": ["sushiruntime", "sushiblas"]})
    closure = checkouts.resolve("sushiai")
    assert closure.missing == (("sushiblas", "sushiai"),)
    assert _owners(closure) == ["sushiruntime", "sushiai"]


@pytest.mark.small
def test_a_checkout_without_a_fragment_is_present_and_empty():
    """Check that a checkout without a fragment is present and adds no source."""
    closure = _Checkouts({"sushiruntime": None, "sushiblas": ["sushiruntime"]}).resolve("sushiblas")
    assert closure.missing == ()
    assert _owners(closure) == ["sushiblas"]


@pytest.mark.small
def test_a_cycle_raises():
    """Check that a cycle raises."""
    checkouts = _Checkouts({"a": ["b"], "b": ["a"]})
    with pytest.raises(ValueError, match="cycle"):
        checkouts.resolve("b")


@pytest.mark.small
def test_a_module_without_its_own_fragment_resolves_to_shared_only():
    """Check that a module without its own fragment resolves to shared only."""
    assert _Checkouts({"bare": None}).resolve("bare").sources == ()
