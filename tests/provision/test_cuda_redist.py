# test_cuda_redist.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""NVIDIA's index is read for its releases and each release for its archives."""

from __future__ import annotations

import json

import pytest

from sushicore.provision.gpu.cuda_redist import RedistError, RedistIndex
from sushicore.provision.gpu.cuda_release import RedistArchive

K_ROOT = "https://example.invalid/redist/"
K_LISTING = ('<a href="redistrib_12.6.3.json">x</a> <a href="redistrib_13.1.2.json">x</a>'
             '<a href="redistrib_13.1.2.json">x</a> <a href="redistrib_9.json.sig">x</a>')
K_MANIFEST = json.dumps({
    "release_label": "13.1.2",
    "cuda_nvcc": {
        "windows-x86_64": {"relative_path": "cuda_nvcc/w/nvcc.zip", "sha256": "aa"},
        "linux-x86_64": {"relative_path": "cuda_nvcc/l/nvcc.tar.xz", "sha256": "bb"},
    },
    "cuda_cudart": {
        "linux-x86_64": {"relative_path": "cuda_cudart/l/rt.tar.xz", "sha256": "cc"},
    },
})


def _index(pages: dict[str, str]) -> RedistIndex:
    """Return an index that serves *pages* and fails on any other URL."""
    def fetch(url):
        """Return the page, or fail as an unreachable host does."""
        if url not in pages:
            raise OSError(f"no route to {url}")
        return pages[url]
    return RedistIndex(fetch, K_ROOT)


def test_versions_lists_each_release_once_newest_first():
    """Check that duplicate links collapse and the order is by number, not text."""
    assert _index({K_ROOT: K_LISTING}).versions() == [(13, 1, 2), (12, 6, 3)]


def test_release_keeps_only_the_archives_of_the_platform():
    """Check that a component without the platform is left out."""
    release = _index({f"{K_ROOT}redistrib_13.1.2.json": K_MANIFEST}).release(
        (13, 1, 2), "windows-x86_64")

    assert release.archives == {
        "cuda_nvcc": RedistArchive(f"{K_ROOT}cuda_nvcc/w/nvcc.zip", "aa"),
    }
    assert release.label == "13.1.2"
    assert release.archives["cuda_nvcc"].file_name == "nvcc.zip"


def test_release_with_a_malformed_manifest_raises():
    """Check that a manifest that is not JSON is a RedistError."""
    index = _index({f"{K_ROOT}redistrib_13.1.2.json": "<html>"})

    with pytest.raises(RedistError):
        index.release((13, 1, 2), "linux-x86_64")


def test_an_unreachable_index_raises():
    """Check that a transport failure is a RedistError."""
    with pytest.raises(RedistError):
        _index({}).versions()

