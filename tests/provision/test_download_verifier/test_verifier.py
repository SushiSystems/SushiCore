# test_verifier.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the verifier of one run: pinned downloads are checked, unpinned ones are named once."""

from __future__ import annotations

import hashlib

import pytest

from sushicore.deps_fragment import Download
from sushicore.errors import ConfigError, DigestMismatchError
from sushicore.provision.download_verifier import (
    DEFAULT_VERIFIER_SLOT,
    DownloadVerifier,
    bind_verifier,
    pinned_download,
    unpinned_downloads,
    verify_download,
)

K_CONTENT = b"an installer"
K_DIGEST = hashlib.sha256(K_CONTENT).hexdigest()
K_WRONG_DIGEST = "0" * 64
K_WINDOWS_TOOLS = ["cmake", "ninja", "doxygen", "git"]


def _file(tmp_path):
    """Write the installer bytes to a file under *tmp_path* and return its path."""
    path = tmp_path / "installer.exe"
    path.write_bytes(K_CONTENT)
    return path


def _warnings(caplog) -> list[str]:
    """Return the warning lines the provision logger recorded."""
    return [record.getMessage() for record in caplog.records
            if record.name.startswith("sushicore.provision") and record.levelname == "WARNING"]


@pytest.mark.medium
def test_a_pinned_download_that_matches_passes_and_is_not_reported(tmp_path, caplog):
    """Check that a matching download raises nothing and is not listed as unverified."""
    verifier = DownloadVerifier({"cmake": K_DIGEST})

    with caplog.at_level("WARNING", logger="sushicore.provision"):
        verifier.verify("cmake", _file(tmp_path))

    assert verifier.unverified() == ()
    assert _warnings(caplog) == []


@pytest.mark.medium
def test_a_pinned_download_that_differs_raises_and_is_deleted(tmp_path):
    """Check that a mismatching download raises and leaves no file to open or run."""
    path = _file(tmp_path)
    verifier = DownloadVerifier({"cmake": K_WRONG_DIGEST})

    with pytest.raises(DigestMismatchError) as raised:
        verifier.verify("cmake", path)

    assert raised.value.expected == K_WRONG_DIGEST
    assert raised.value.actual == K_DIGEST
    assert not path.exists()


@pytest.mark.medium
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


@pytest.mark.medium
def test_an_unpinned_download_is_reported_once_per_run(tmp_path, caplog):
    """Check that fetching one unpinned download twice draws one warning."""
    verifier = DownloadVerifier({})

    with caplog.at_level("WARNING", logger="sushicore.provision"):
        verifier.verify("ninja", _file(tmp_path))
        verifier.verify("ninja", _file(tmp_path))
        verifier.verify("git", _file(tmp_path))

    assert verifier.unverified() == ("ninja", "git")
    assert len(_warnings(caplog)) == 2


@pytest.mark.medium
def test_verify_download_goes_through_the_bound_verifier(tmp_path):
    """Check that the module-level call uses the verifier a run bound."""
    with DEFAULT_VERIFIER_SLOT.holding(DownloadVerifier({"cmake": K_WRONG_DIGEST})):
        with pytest.raises(DigestMismatchError):
            verify_download("cmake", _file(tmp_path))


@pytest.mark.medium
def test_unbinding_leaves_a_verifier_that_pins_nothing(tmp_path, caplog):
    """Check that with no run bound a download proceeds and is still reported."""
    DEFAULT_VERIFIER_SLOT.bind(None)

    with caplog.at_level("WARNING", logger="sushicore.provision"):
        verify_download("cmake", _file(tmp_path))

    assert len(_warnings(caplog)) == 1


@pytest.mark.small
def test_unpinned_downloads_lists_the_declared_tools_with_no_digest():
    """Check that the Windows tools a fragment declares are listed, and none it leaves out."""
    assert unpinned_downloads(set(K_WINDOWS_TOOLS), {}, "windows") == K_WINDOWS_TOOLS
    assert unpinned_downloads(set(), {}, "windows") == []


@pytest.mark.small
def test_unpinned_downloads_lists_a_declared_toolchain_with_no_digest():
    """Check that a declared toolchain joins the list and an undeclared one does not."""
    listed = unpinned_downloads({"intel-llvm", "hwloc"}, {}, "windows")

    assert "intel-llvm" in listed
    assert "oneapi" not in listed and "hwloc" not in listed


@pytest.mark.small
def test_unpinned_downloads_leaves_out_what_is_pinned():
    """Check that a pinned download is not listed."""
    digests = {"cmake": K_DIGEST, "intel-llvm": K_DIGEST}

    listed = unpinned_downloads({"cmake", "ninja", "intel-llvm"}, digests, "windows")

    assert listed == ["ninja"]


@pytest.mark.small
def test_unpinned_downloads_on_linux_names_only_the_declared_bundle():
    """Check that Linux, which fetches one bundle directly, lists that alone."""
    assert unpinned_downloads(set(), {}, "linux") == []
    assert unpinned_downloads({"intel-llvm", "oneapi", "cuda"}, {}, "linux") == ["intel-llvm"]



@pytest.mark.small
def test_pinned_returns_the_download_an_entry_pins():
    """Check that the verifier answers the pinned download of the entry it is asked for."""
    pinned = Download("cmake", "v1", "https://example.invalid/c.zip", K_DIGEST)
    assert DownloadVerifier({}, {"cmake": pinned}).pinned("cmake") == pinned


@pytest.mark.small
def test_pinned_names_the_entry_when_no_fragment_pins_it():
    """Check that an entry no fragment pins is refused, with its name in the message."""
    with pytest.raises(ConfigError) as refused:
        DownloadVerifier({}).pinned("cmake")
    assert "'cmake'" in str(refused.value)


@pytest.mark.small
def test_pinned_download_reads_the_bound_verifier():
    """Check that the module function answers from the verifier bound for the run."""
    pinned = Download("git", "v2", "https://example.invalid/g.exe", K_DIGEST)
    with DEFAULT_VERIFIER_SLOT.holding(DownloadVerifier({}, {"git": pinned})):
        assert pinned_download("git") == pinned


@pytest.mark.small
def test_pinned_download_prefers_the_verifier_it_is_passed():
    """Check that an explicit verifier answers before the default slot's."""
    pinned = Download("git", "v2", "https://example.invalid/g.exe", K_DIGEST)
    assert pinned_download("git", verifier=DownloadVerifier({}, {"git": pinned})) == pinned


@pytest.mark.medium
def test_verify_download_prefers_the_verifier_it_is_passed(tmp_path):
    """Check that an explicit verifier checks the file instead of the default slot's."""
    with pytest.raises(DigestMismatchError):
        verify_download("cmake", _file(tmp_path),
                        verifier=DownloadVerifier({"cmake": K_WRONG_DIGEST}))


@pytest.mark.small
def test_bind_verifier_warns_and_binds_the_default_slot():
    """Check that the deprecated binder warns and still sets what the sites read."""
    verifier = DownloadVerifier({})
    try:
        with pytest.warns(DeprecationWarning, match="bind_verifier"):
            bind_verifier(verifier)
        assert DEFAULT_VERIFIER_SLOT.current() is verifier
    finally:
        DEFAULT_VERIFIER_SLOT.bind(None)
