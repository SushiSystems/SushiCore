# test_download_verifier.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the verifier of one run: pinned downloads are checked, unpinned ones are named once."""

from __future__ import annotations

import hashlib

import pytest

from sushicore.errors import DigestMismatchError
from sushicore.provision import download_verifier
from sushicore.provision.download_verifier import (
    DownloadVerifier,
    bind_verifier,
    unpinned_downloads,
    verify_download,
)

K_CONTENT = b"an installer"
K_DIGEST = hashlib.sha256(K_CONTENT).hexdigest()
K_WRONG_DIGEST = "0" * 64


def _file(tmp_path):
    """Write the installer bytes to a file under *tmp_path* and return its path."""
    path = tmp_path / "installer.exe"
    path.write_bytes(K_CONTENT)
    return path


def _warnings(caplog) -> list[str]:
    """Return the warning lines the provision logger recorded."""
    return [record.getMessage() for record in caplog.records
            if record.name == "sushicore.provision" and record.levelname == "WARNING"]


def test_a_pinned_download_that_matches_passes_and_is_not_reported(tmp_path, caplog):
    """Check that a matching download raises nothing and is not listed as unverified."""
    verifier = DownloadVerifier({"cmake": K_DIGEST})

    with caplog.at_level("WARNING", logger="sushicore.provision"):
        verifier.verify("cmake", _file(tmp_path))

    assert verifier.unverified() == ()
    assert _warnings(caplog) == []


def test_a_pinned_download_that_differs_raises_and_is_deleted(tmp_path):
    """Check that a mismatching download raises and leaves no file to open or run."""
    path = _file(tmp_path)
    verifier = DownloadVerifier({"cmake": K_WRONG_DIGEST})

    with pytest.raises(DigestMismatchError) as raised:
        verifier.verify("cmake", path)

    assert raised.value.expected == K_WRONG_DIGEST
    assert raised.value.actual == K_DIGEST
    assert not path.exists()


def test_an_unpinned_download_passes_and_is_warned_about_by_name(tmp_path, caplog):
    """Check that a download with no digest proceeds and is reported at warning level."""
    path = _file(tmp_path)
    verifier = DownloadVerifier({})

    with caplog.at_level("WARNING", logger="sushicore.provision"):
        verifier.verify("ninja", path)

    assert path.exists()
    assert verifier.unverified() == ("ninja",)
    (warning,) = _warnings(caplog)
    assert "ninja" in warning and "sha256" in warning


def test_an_unpinned_download_is_reported_once_per_run(tmp_path, caplog):
    """Check that fetching one unpinned download twice draws one warning."""
    verifier = DownloadVerifier({})

    with caplog.at_level("WARNING", logger="sushicore.provision"):
        verifier.verify("ninja", _file(tmp_path))
        verifier.verify("ninja", _file(tmp_path))
        verifier.verify("git", _file(tmp_path))

    assert verifier.unverified() == ("ninja", "git")
    assert len(_warnings(caplog)) == 2


def test_verify_download_goes_through_the_bound_verifier(tmp_path):
    """Check that the module-level call uses the verifier a run bound."""
    bind_verifier(DownloadVerifier({"cmake": K_WRONG_DIGEST}))
    try:
        with pytest.raises(DigestMismatchError):
            verify_download("cmake", _file(tmp_path))
    finally:
        bind_verifier(None)


def test_unbinding_leaves_a_verifier_that_pins_nothing(tmp_path, caplog):
    """Check that with no run bound a download proceeds and is still reported."""
    bind_verifier(None)

    with caplog.at_level("WARNING", logger="sushicore.provision"):
        verify_download("cmake", _file(tmp_path))

    assert len(_warnings(caplog)) == 1
    bind_verifier(None)


def test_unpinned_downloads_lists_the_tools_windows_always_fetches():
    """Check that the Windows tools are listed whether or not a fragment declares them."""
    assert unpinned_downloads(set(), {}, "windows") == ["cmake", "ninja", "doxygen", "git"]


def test_unpinned_downloads_lists_a_declared_toolchain_with_no_digest():
    """Check that a declared toolchain joins the list and an undeclared one does not."""
    listed = unpinned_downloads({"intel-llvm", "hwloc"}, {}, "windows")

    assert "intel-llvm" in listed
    assert "oneapi" not in listed and "hwloc" not in listed


def test_unpinned_downloads_leaves_out_what_is_pinned():
    """Check that a pinned download is not listed."""
    digests = {"cmake": K_DIGEST, "intel-llvm": K_DIGEST}

    listed = unpinned_downloads({"intel-llvm"}, digests, "windows")

    assert listed == ["ninja", "doxygen", "git"]


def test_unpinned_downloads_on_linux_names_only_the_declared_bundle():
    """Check that Linux, which fetches one bundle directly, lists that alone."""
    assert unpinned_downloads(set(), {}, "linux") == []
    assert unpinned_downloads({"intel-llvm", "oneapi", "cuda"}, {}, "linux") == ["intel-llvm"]


def test_every_download_name_is_listed_for_some_platform():
    """Check that the two tables cover the eight downloads the installers name."""
    named = {name for table in (download_verifier.K_TOOL_DOWNLOADS,
                                download_verifier.K_DECLARED_DOWNLOADS)
             for names in table.values() for name in names}

    assert named == {"cmake", "ninja", "doxygen", "git",
                     "intel-llvm", "adaptivecpp", "oneapi", "cuda"}
