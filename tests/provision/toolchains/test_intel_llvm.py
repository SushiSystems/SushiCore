# test_intel_llvm.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Fake-backed tests for the intel/llvm installer."""

from __future__ import annotations

import ast

import io

import re

import tarfile

from pathlib import Path

import pytest

from sushicore import provision

from sushicore.provision.config import ProvisionSettings

from sushicore.provision.toolchains import intel_llvm

from sushicore.provision.toolchains.stamp import read_toolchain_stamp, toolchains_dir



pytestmark = pytest.mark.medium



class _StatusContext:
    """A no-op stand-in for the Rich ``console.status`` context manager."""

    def __enter__(self):
        """Return this context unchanged."""
        return self

    def __exit__(self, *exc_info):
        """Swallow nothing; let any exception propagate."""
        return False



class _InnerConsole:
    """Stands in for ``Console.console``, the raw Rich console."""

    def print(self, *args, **kwargs):
        """Discard the call."""

    def status(self, *args, **kwargs):
        """Return a no-op status context."""
        return _StatusContext()



class FakeConsole:
    """Records every semantic call; answers ``is_machine``/``prompt`` on demand."""

    def __init__(self, machine: bool = False, answer: str = "n") -> None:
        """Start with no recorded calls, in interactive mode by default."""
        self.calls: list[tuple[str, tuple]] = []
        self.console = _InnerConsole()
        self._machine = machine
        self._answer = answer

    def __getattr__(self, name: str):
        """Return a recorder for any semantic console method name."""
        def record(*args, **_kwargs):
            """Check that record."""
            self.calls.append((name, args))
        return record

    def is_machine(self) -> bool:
        """Report the fixed machine-mode flag this fake was built with."""
        return self._machine

    def prompt(self, _message: str, _default: str) -> str:
        """Return the fixed answer this fake was built with."""
        return self._answer

    def has_call(self, name: str) -> bool:
        """Report whether *name* was recorded at least once."""
        return any(call[0] == name for call in self.calls)



@pytest.fixture
def fake_console():
    """Bind a :class:`FakeConsole` for the test, then unbind it."""
    fake = FakeConsole()
    provision.bind_console(lambda: fake)
    yield fake
    provision.bind_console(None)



def _linux_cfg() -> ProvisionSettings:
    """Check that linux cfg."""
    return ProvisionSettings(platform="linux")



def test_install_intel_llvm_reuses_an_existing_bundle(provision_home, fake_console, monkeypatch):
    """Check that install intel llvm reuses an existing bundle."""
    root = toolchains_dir() / "llvm-sycl"
    (root / "bin").mkdir(parents=True)
    (root / "bin" / "clang++").touch()
    monkeypatch.setattr(intel_llvm, "gh_latest_release_asset",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no network")))

    result = intel_llvm.install_intel_llvm(_linux_cfg(), dry_run=False)

    assert result == str(root)
    assert fake_console.has_call("warn")  # no sanitizer runtime in the fake tree



def test_install_intel_llvm_dry_run_reports_without_downloading(provision_home, fake_console):
    """Check that install intel llvm dry run reports without downloading."""
    root = toolchains_dir() / "llvm-sycl"

    result = intel_llvm.install_intel_llvm(_linux_cfg(), dry_run=True)

    assert result == str(root)
    assert not root.exists()
    assert fake_console.has_call("info")



def test_install_intel_llvm_refresh_skips_when_tag_unchanged(provision_home, fake_console,
                                                              monkeypatch):
    """Check that install intel llvm refresh skips when tag unchanged."""
    root = toolchains_dir() / "llvm-sycl"
    (root / "bin").mkdir(parents=True)
    (root / "bin" / "clang++").touch()
    from sushicore.provision.toolchains.stamp import write_toolchain_stamp
    write_toolchain_stamp(root, "intel/llvm", "nightly-1")
    monkeypatch.setattr(intel_llvm, "gh_latest_release_asset",
                        lambda *a, **k: ("nightly-1", "http://example.invalid/a"))
    monkeypatch.setattr(intel_llvm, "download",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no download")))

    result = intel_llvm.install_intel_llvm(_linux_cfg(), dry_run=False, refresh=True)

    assert result == str(root)



def test_install_intel_llvm_downloads_and_extracts_on_first_install(provision_home, fake_console,
                                                                     monkeypatch):
    """Check that install intel llvm downloads and extracts on first install."""
    root = toolchains_dir() / "llvm-sycl"
    clang = root / "bin" / "clang++"
    monkeypatch.setattr(intel_llvm, "gh_latest_release_asset",
                        lambda *a, **k: ("nightly-2", "http://example.invalid/a"))
    monkeypatch.setattr(intel_llvm, "download", lambda *a, **k: None)

    def fake_extract(archive, dest):
        """Check that fake extract."""
        (dest / "bin").mkdir(parents=True, exist_ok=True)
        (dest / "bin" / "clang++").touch()

    monkeypatch.setattr(intel_llvm, "_extract_tar_gz", fake_extract)

    result = intel_llvm.install_intel_llvm(_linux_cfg(), dry_run=False)

    assert result == str(root)
    assert clang.is_file()
    assert read_toolchain_stamp(root)["tag"] == "nightly-2"



def test_install_intel_llvm_returns_none_when_asset_resolution_fails(provision_home, fake_console,
                                                                      monkeypatch):
    """Check that install intel llvm returns none when asset resolution fails."""
    monkeypatch.setattr(intel_llvm, "gh_latest_release_asset",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no asset")))

    result = intel_llvm.install_intel_llvm(_linux_cfg(), dry_run=False)

    assert result is None
    assert fake_console.has_call("error")



def test_install_intel_llvm_cleans_up_on_download_failure_without_refresh(
        provision_home, fake_console, monkeypatch):
    """Check that install intel llvm cleans up on download failure without refresh."""
    root = toolchains_dir() / "llvm-sycl"
    monkeypatch.setattr(intel_llvm, "gh_latest_release_asset",
                        lambda *a, **k: ("nightly-2", "http://example.invalid/a"))
    monkeypatch.setattr(intel_llvm, "download",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("network down")))
    root.mkdir(parents=True)
    (root / "stray-file").touch()

    result = intel_llvm.install_intel_llvm(_linux_cfg(), dry_run=False)

    assert result is None
    assert not root.exists()



def _make_tar_gz(tmp_path: Path, wrapped: bool) -> Path:
    """Check that make tar gz."""
    archive = tmp_path / "bundle.tar.gz"
    names = (["wrap/bin/clang++"] if wrapped
             else ["bin/clang++", "lib/libsomething.so"])
    with tarfile.open(archive, "w:gz") as tf:
        data = b"binary"
        for name in names:
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return archive



def test_extract_tar_gz_collapses_a_single_top_level_wrapper_dir(tmp_path):
    """Check that extract tar gz collapses a single top level wrapper dir."""
    archive = _make_tar_gz(tmp_path, wrapped=True)
    dest = tmp_path / "dest"

    intel_llvm._extract_tar_gz(archive, dest)

    assert (dest / "bin" / "clang++").is_file()



def test_extract_tar_gz_leaves_an_unwrapped_layout_alone(tmp_path):
    """Check that extract tar gz leaves an unwrapped layout alone."""
    archive = _make_tar_gz(tmp_path, wrapped=False)
    dest = tmp_path / "dest"

    intel_llvm._extract_tar_gz(archive, dest)

    assert (dest / "bin" / "clang++").is_file()



def test_intel_llvm_defines_no_unused_private_function():
    """Check that intel llvm defines no unused private function."""
    source = Path(intel_llvm.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    private = [node.name for node in tree.body
               if isinstance(node, ast.FunctionDef) and node.name.startswith("_")]
    unused = [name for name in private if len(re.findall(rf"\b{name}\b", source)) < 2]
    assert unused == []
