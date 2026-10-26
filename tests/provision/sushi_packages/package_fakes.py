# package_fakes.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Builders shared by the package tests: keys, installed packages and a clock."""

from __future__ import annotations

import contextlib
from pathlib import Path

from sushicore.provision.sushi_packages.closure_walk import ClosureWalk
from sushicore.provision.sushi_packages.configure_inputs import ConfigureInputs
from sushicore.provision.sushi_packages.forced_packages import ForcedPackages
from sushicore.provision.sushi_packages.key_factory import KeyFactory
from sushicore.provision.sushi_packages.link_publisher import LinkPublisher
from sushicore.provision.sushi_packages.package import Package
from sushicore.provision.sushi_packages.package_builder import BuildRequest
from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.package_locks import PackageLocks
from sushicore.provision.sushi_packages.package_request import PackageRequest
from sushicore.provision.sushi_packages.package_resolver import PackageResolver
from sushicore.provision.sushi_packages.source_locator import SushiSourceLocator
from sushicore.provision.sushi_packages.stable_link import StableLink
from sushicore.provision.sushi_packages.package_key import PackageKey
from sushicore.provision.sushi_packages.package_store import PackageStore

#: The spelling of each library's package, as its config folder carries it.
K_SPELLING = {"sushilog": "SushiLog", "sushiruntime": "SushiRuntime", "sushiblas": "SushiBLAS"}


class Clock:
    """A clock that moves only when told to."""

    def __init__(self, now: float = 1000.0) -> None:
        """Start at *now* seconds."""
        self.now = now

    def __call__(self) -> float:
        """Return the current time."""
        return self.now


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


class ListInspector:
    """Lists every file of a checkout, as git would with nothing ignored."""

    def files(self, checkout: Path) -> list[Path]:
        """Return every file below *checkout*, relative to it."""
        return sorted(p.relative_to(checkout) for p in checkout.rglob("*") if p.is_file())


class FakeBuilder:
    """Installs a package with a config folder instead of running a CLI."""

    def __init__(self, fail: bool = False) -> None:
        """Record requests; raise on each build when *fail*."""
        self.requests: list[BuildRequest] = []
        self.fail = fail

    def build(self, request: BuildRequest) -> None:
        """Record *request* and fill its prefix like an install would."""
        self.requests.append(request)
        if self.fail:
            raise PackageError("the build failed")
        spelling = K_SPELLING.get(request.key.name, request.key.name)
        config = request.prefix / "lib" / "cmake" / spelling
        config.mkdir(parents=True)
        (config / f"{spelling}Config.cmake").write_text("", encoding="utf-8")
        (request.prefix / "bin").mkdir()


@contextlib.contextmanager
def no_lock(_path, _timeout):
    """Stand in for the file lock."""
    yield


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
    """A workspace of libraries and a resolver over a temporary store."""

    def __init__(self, tmp_path: Path, env=None, builder: FakeBuilder | None = None) -> None:
        """Lay out sushilog, sushiruntime, sushiblas and the consumer sushiai."""
        self.workspace = tmp_path / "ws"
        self.workspace.mkdir()
        make_library(self.workspace, "sushilog")
        make_library(self.workspace, "sushiruntime", ("sushilog",))
        make_library(self.workspace, "sushiblas", ("sushiruntime", "sushilog"))
        self.consumer = make_library(self.workspace, "sushiai", ("sushiblas", "sushiruntime"),
                                     cli="")
        self.root = tmp_path / "packages"
        self.builder = builder or FakeBuilder()
        self.lines: list[str] = []
        self.warnings: list[str] = []
        self.store = PackageStore(self.root, keep=3, clock=Clock(), sleep=lambda _s: None)
        self.resolver = self._resolver(env or {})

    def _resolver(self, env) -> PackageResolver:
        """Assemble a resolver over the rig's store, with *env* as the nested environment."""
        locks = PackageLocks(self.root, factory=no_lock)
        keys = KeyFactory(ListInspector(), ConfigureInputs(lambda: "3.28.1", lambda _r: ""),
                          lambda _compiler: "tc", "1")
        return PackageResolver(
            ClosureWalk(SushiSourceLocator()), keys, self.store, self.builder,
            ForcedPackages(env, self.store, self.warnings.append), locks,
            LinkPublisher(locks, StableLink(self.root)), self.lines.append)

    def nested(self, env) -> None:
        """Replace the resolver with one that sees *env* as its environment."""
        self.resolver = self._resolver(env)

    def request(self, **changes) -> PackageRequest:
        """Return the request of the consumer, with *changes* applied."""
        values = {"owner": "sushiai", "root": self.consumer, "compiler": "clang++",
                  "build_type": "Release"}
        values.update(changes)
        return PackageRequest(**values)
