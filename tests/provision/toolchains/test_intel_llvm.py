# test_intel_llvm.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The intel/llvm installer reuses, refreshes, downloads and cleans up a bundle under the toolchains folder."""

from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from sushicore.deps_fragment import Download
from sushicore.errors import ConfigError
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.install_location import ToolkitInstall
from sushicore.provision.toolchains import intel_llvm
from sushicore.provision.toolchains.stamp import (
    read_toolchain_stamp, toolchains_dir, write_toolchain_stamp)

pytestmark = pytest.mark.medium

_URL = "http://example.invalid/a"
_RAW_PREFIX = "https://raw.githubusercontent.com/intel/llvm/"
_LICENCE_TEXT = "Apache License 2.0\n\n--- LLVM Exceptions to the Apache 2.0 License ----\n"
_LICENCE_PATH = Path("share") / "licenses" / "llvm-sycl" / "llvm" / "LICENSE.TXT"


class _Pinner:
    """Answers a pin lookup with a fixed tag and counts the lookups."""

    def __init__(self, tag: str = "nightly-2", error: Exception | None = None) -> None:
        """Answer *tag*, or raise *error* when one is given."""
        self._tag = tag
        self._error = error
        self.lookups = 0

    def __call__(self, name: str) -> Download:
        """Count the lookup and answer the pinned download."""
        self.lookups += 1
        if self._error is not None:
            raise self._error
        return Download(name, self._tag, _URL, "0" * 64)


class _Fetcher:
    """Writes a tar.gz of the named members as the download, or raises *error*; counts the downloads.

    A raw GitHub URL, the licence text, is answered with *licence_text* or *licence_error* and
    listed in ``licence_urls``, so no test reaches the network.
    """

    def __init__(self, members: tuple[str, ...] | dict[str, bytes] = (),
                 error: Exception | None = None, licence_text: str = _LICENCE_TEXT,
                 licence_error: Exception | None = None) -> None:
        """Download an archive holding *members* (a name, or a name with its bytes), or fail with *error*."""
        self._members = (dict(members) if isinstance(members, dict)
                         else {name: b"binary" for name in members})
        self._error = error
        self._licence_text = licence_text
        self._licence_error = licence_error
        self.downloads = 0
        self.licence_urls: list[str] = []

    def __call__(self, url: str, dest: Path) -> None:
        """Count the download and write the archive to *dest*."""
        if url.startswith(_RAW_PREFIX):
            self.licence_urls.append(url)
            if self._licence_error is not None:
                raise self._licence_error
            dest.write_text(self._licence_text, encoding="utf-8")
            return
        self.downloads += 1
        if self._error is not None:
            raise self._error
        with tarfile.open(dest, "w:gz") as archive:
            for name, data in self._members.items():
                info = tarfile.TarInfo(name=name)
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))


def _linux_cfg() -> ProvisionSettings:
    """Build the configuration of a Linux host."""
    return ProvisionSettings(platform="linux")


def _install_clang(root: Path) -> None:
    """Put an empty compiler in the bundle folder, as an earlier install would have."""
    (root / "bin").mkdir(parents=True)
    (root / "bin" / "clang++").touch()


def test_install_intel_llvm_reuses_an_existing_bundle(provision_home, recording_console):
    """Check that an installed bundle is returned with a warning and no release lookup."""
    root = toolchains_dir() / "llvm-sycl"
    _install_clang(root)
    pinner = _Pinner()

    result = intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False, pin=pinner, console=recording_console)

    assert result == str(root)
    assert pinner.lookups == 0
    assert recording_console.has_call("warn")  # no sanitizer runtime in the tree


def test_install_intel_llvm_dry_run_reports_without_downloading(provision_home, recording_console):
    """Check that a dry run names the bundle folder, downloads nothing and creates nothing."""
    root = toolchains_dir() / "llvm-sycl"
    fetcher = _Fetcher()

    result = intel_llvm.install_intel_llvm(_linux_cfg(), dry_run=True, fetch=fetcher,
                                           console=recording_console)

    assert result == str(root)
    assert fetcher.downloads == 0
    assert not root.exists()
    assert recording_console.has_call("info")


def test_install_intel_llvm_refresh_skips_when_tag_unchanged(provision_home, recording_console):
    """Check that a refresh at the recorded tag downloads nothing."""
    root = toolchains_dir() / "llvm-sycl"
    _install_clang(root)
    write_toolchain_stamp(root, "intel/llvm", "nightly-1")
    fetcher = _Fetcher()

    result = intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False, refresh=True,
        pin=_Pinner("nightly-1"), fetch=fetcher, console=recording_console)

    assert result == str(root)
    assert fetcher.downloads == 0


def test_install_intel_llvm_downloads_and_extracts_on_first_install(
        provision_home, recording_console):
    """Check that a first install extracts the bundle and records its tag."""
    root = toolchains_dir() / "llvm-sycl"

    result = intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False,
        pin=_Pinner("nightly-2"), fetch=_Fetcher(("bin/clang++",
                                                  "lib/libsomething.so")),
                                                  console=recording_console)

    assert result == str(root)
    assert (root / "bin" / "clang++").is_file()
    assert read_toolchain_stamp(root)["tag"] == "nightly-2"


def test_install_intel_llvm_stops_when_no_fragment_pins_the_bundle(
        provision_home, recording_console):
    """Check that a missing pin reaches the caller as the error that names the entry."""
    with pytest.raises(ConfigError):
        intel_llvm.install_intel_llvm(
            _linux_cfg(), dry_run=False, pin=_Pinner(error=ConfigError("no pin 'intel-llvm'")),
            console=recording_console)


def test_install_intel_llvm_cleans_up_on_download_failure_without_refresh(
        provision_home, recording_console):
    """Check that a failed first download removes the half-made bundle folder."""
    root = toolchains_dir() / "llvm-sycl"
    root.mkdir(parents=True)
    (root / "stray-file").touch()

    result = intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False,
        pin=_Pinner(), fetch=_Fetcher(error=OSError("network down")), console=recording_console)

    assert result is None
    assert not root.exists()


def test_install_intel_llvm_collapses_a_single_top_level_wrapper_dir(
        provision_home, recording_console):
    """Check that an archive wrapped in one folder installs with its contents at the bundle root."""
    root = toolchains_dir() / "llvm-sycl"

    intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False,
        pin=_Pinner(), fetch=_Fetcher(("wrap/bin/clang++",)), console=recording_console)

    assert (root / "bin" / "clang++").is_file()
    assert not (root / "wrap").exists()


def test_install_intel_llvm_leaves_an_unwrapped_layout_alone(provision_home, recording_console):
    """Check that an archive with several top-level folders installs them as they are."""
    root = toolchains_dir() / "llvm-sycl"

    intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False,
        pin=_Pinner(),
        fetch=_Fetcher(("bin/clang++", "lib/libsomething.so")), console=recording_console)

    assert (root / "bin" / "clang++").is_file()
    assert (root / "lib" / "libsomething.so").is_file()


def test_locate_reports_the_installed_bundle_with_its_stamped_tag(provision_home):
    """Check that locate returns the bundle root and the tag its stamp records."""
    root = toolchains_dir() / "llvm-sycl"
    _install_clang(root)
    write_toolchain_stamp(root, "intel/llvm", "nightly-7")

    assert intel_llvm.INTEL_LLVM.locate(_linux_cfg()) == ToolkitInstall(root, "nightly-7")


def test_locate_reports_nothing_when_the_bundle_has_no_compiler(provision_home):
    """Check that locate returns None for a toolchains folder with no bundle."""
    assert intel_llvm.INTEL_LLVM.locate(_linux_cfg()) is None


def test_a_first_install_fetches_llvms_licence_text_at_the_pinned_tag(
        provision_home, recording_console):
    """Check that a bundle without a licence file gets LLVM's text from intel/llvm at its pinned tag."""
    root = toolchains_dir() / "llvm-sycl"
    fetcher = _Fetcher(("bin/clang++",))

    intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False, pin=_Pinner("nightly-2"), fetch=fetcher,
        console=recording_console)

    assert (root / _LICENCE_PATH).read_text(encoding="utf-8") == _LICENCE_TEXT
    assert fetcher.licence_urls == [
        "https://raw.githubusercontent.com/intel/llvm/nightly-2/llvm/LICENSE.TXT"]


def test_a_licence_file_the_bundle_carries_is_installed_without_a_fetch(
        provision_home, recording_console):
    """Check that a LICENSE.TXT at the bundle root is copied and nothing is fetched for it."""
    root = toolchains_dir() / "llvm-sycl"
    bundled = _LICENCE_TEXT + "bundled\n"
    fetcher = _Fetcher({"bin/clang++": b"binary", "LICENSE.TXT": bundled.encode()})

    intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False, pin=_Pinner(), fetch=fetcher, console=recording_console)

    assert (root / _LICENCE_PATH).read_text(encoding="utf-8") == bundled
    assert fetcher.licence_urls == []


def test_a_licence_text_that_cannot_be_fetched_fails_the_install_and_removes_the_bundle(
        provision_home, recording_console):
    """Check that a failed licence fetch returns None, names the licence and leaves no bundle."""
    root = toolchains_dir() / "llvm-sycl"

    result = intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False, pin=_Pinner(),
        fetch=_Fetcher(("bin/clang++",), licence_error=OSError("offline")),
        console=recording_console)

    assert result is None
    assert not root.exists()
    assert any("licence text" in text for text in recording_console.texts("error"))


@pytest.mark.parametrize("text", ["", "an unrelated page\n", "Apache License 2.0 without the clause\n"])
def test_a_fetched_text_that_is_not_the_licence_is_never_installed(
        provision_home, recording_console, text):
    """Check that an empty or foreign text fails the install and writes no licence file."""
    root = toolchains_dir() / "llvm-sycl"

    result = intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False, pin=_Pinner(),
        fetch=_Fetcher(("bin/clang++",), licence_text=text), console=recording_console)

    assert result is None
    assert not (root / _LICENCE_PATH).exists()
