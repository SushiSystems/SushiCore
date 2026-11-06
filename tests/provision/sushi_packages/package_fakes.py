# package_fakes.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Builders shared by the package tests: keys, installed packages and a rig."""

from __future__ import annotations

from pathlib import Path

from sushicore.provision.sushi_packages.clock_memory import ManualClock
from sushicore.provision.sushi_packages.closure_walk import ClosureWalk
from sushicore.provision.sushi_packages.configure_inputs import (
    ConfigureInputs,
    MemoryCMakeVersion,
    MemoryVcpkgHead,
)
from sushicore.provision.sushi_packages.forced_packages import ForcedPackages
from sushicore.provision.sushi_packages.key_factory import KeyFactory
from sushicore.provision.sushi_packages.lines_memory import RecordedLines
from sushicore.provision.sushi_packages.link_publisher import LinkPublisher
from sushicore.provision.sushi_packages.package import Package
from sushicore.provision.sushi_packages.package_builder import RecordingBuilder
from sushicore.provision.sushi_packages.package_key import PackageKey
from sushicore.provision.sushi_packages.package_locks import MemoryLocks, PackageLocks
from sushicore.provision.sushi_packages.package_request import PackageRequest
from sushicore.provision.sushi_packages.package_resolver import PackageResolver
from sushicore.provision.sushi_packages.package_store import PackageStore
from sushicore.provision.sushi_packages.source_locator import SushiSourceLocator
from sushicore.provision.sushi_packages.source_state import MemoryInspector
from sushicore.provision.sushi_packages.stable_link import StableLink
from sushicore.provision.sushi_packages.toolchain_identity import MemoryIdentity

#: The spelling of each library's package, as its config folder carries it.
K_SPELLING = {"sushilog": "SushiLog", "sushiruntime": "SushiRuntime", "sushiblas": "SushiBLAS"}

#: The files git lists in the checkout of a library the rig lays out.
K_TRACKED = (Path("src/a.cpp"), Path("cli/sushistack.deps.toml"))

#: The seconds each build of the rig takes on its clock.
K_BUILD_SECONDS = 2.5


def make_key(name: str = "sushiruntime", source: str = "s1", **changes) -> PackageKey:
    """Return a key of *name* at *source*, with *changes* applied to its other parts."""
    parts = {"toolchain": "tc", "build_type": "release", "recipe": "lean-1", "inputs": "in"}
    parts.update(changes)
    return PackageKey(name, source, **parts)


def install(store: PackageStore, key: PackageKey, seconds: float = 1.0) -> Package:
    """Stage, fill and commit the package of *key*, with a config folder and a bin folder."""
    prefix = store.stage(key)
    spelling = K_SPELLING.get(key.name, key.name)
    config = prefix / "lib" / "cmake" / spelling
    config.mkdir(parents=True)
    (config / f"{spelling}Config.cmake").write_text("", encoding="utf-8")
    (prefix / "bin").mkdir()
    return store.commit(key, seconds)


def make_library(workspace: Path, name: str, depends_on=(), cli: str = "x") -> Path:
    """Create the checkout of *name* beside the others, with a fragment and one source file."""
    checkout = workspace / name
    (checkout / "cli").mkdir(parents=True, exist_ok=True)
    (checkout / "src").mkdir(exist_ok=True)
    (checkout / "src" / "a.cpp").write_text(f"// {name}", encoding="utf-8")
    names = ", ".join(f'"{dep}"' for dep in depends_on)
    lines = ["[module]", *([f'cli = "{cli}"'] if cli else []), f"depends_on = [{names}]"]
    (checkout / "cli" / "sushistack.deps.toml").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    return checkout


class Rig:
    """A workspace of libraries and a resolver over a temporary store.

    Everything the resolver reaches through a port is an in-memory adapter: the builder, the
    locks, the source inspector, the probes, the clock and the two line sinks.
    """

    def __init__(self, tmp_path: Path, env=None, fail: bool = False) -> None:
        """Lay out sushilog, sushiruntime, sushiblas and the consumer sushiai."""
        self.workspace = tmp_path / "ws"
        self.workspace.mkdir()
        self.inspector = MemoryInspector({})
        self._library("sushilog")
        self._library("sushiruntime", ("sushilog",))
        self._library("sushiblas", ("sushiruntime", "sushilog"))
        self.consumer = make_library(self.workspace, "sushiai", ("sushiblas", "sushiruntime"),
                                     cli="")
        self.root = tmp_path / "packages"
        self.clock = ManualClock()
        self.builder = RecordingBuilder(K_SPELLING, fail, self.clock.advance, K_BUILD_SECONDS)
        self.lines = RecordedLines()
        self.warnings = RecordedLines()
        self.store = PackageStore(self.root, keep=3, clock=self.clock, sleep=lambda _s: None)
        self.resolver = self._resolver(env or {})

    def _library(self, name: str, depends_on=()) -> None:
        """Create the checkout of *name* and list the files git would list in it."""
        checkout = make_library(self.workspace, name, depends_on)
        self.inspector.listing[checkout.resolve()] = list(K_TRACKED)

    def _resolver(self, env) -> PackageResolver:
        """Assemble a resolver over the rig's store, with *env* as the nested environment."""
        locks = PackageLocks(self.root, factory=MemoryLocks())
        keys = KeyFactory(self.inspector,
                          ConfigureInputs(MemoryCMakeVersion(), MemoryVcpkgHead()),
                          MemoryIdentity("tc"), "1")
        return PackageResolver(
            ClosureWalk(SushiSourceLocator()), keys, self.store, self.builder,
            ForcedPackages(env, self.store, self.warnings), locks,
            LinkPublisher(locks, StableLink(self.root)), self.lines, self.clock)

    def nested(self, env) -> None:
        """Replace the resolver with one that sees *env* as its environment."""
        self.resolver = self._resolver(env)

    def edit(self, library: str, relative: str, text: str) -> None:
        """Write *text* to a file of *library* and list it, as git lists a file it sees."""
        checkout = self.workspace / library
        path = checkout / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        listing = self.inspector.listing[checkout.resolve()]
        if Path(relative) not in listing:
            listing.append(Path(relative))

    def request(self, **changes) -> PackageRequest:
        """Return the request of the consumer, with *changes* applied."""
        values = {"owner": "sushiai", "root": self.consumer, "compiler": "clang++",
                  "build_type": "Release"}
        values.update(changes)
        return PackageRequest(**values)
