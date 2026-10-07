# producer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Produces a repository's documentation bundle: stage, describe, pack."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, final

from .api_reference import ApiSource, stage_api
from .bundle_archive import write_archive
from .bundle_manifest import K_API_ROOT, K_PAGES_DIR, BundleIdentity, build_manifest
from .errors import ReleaseError
from .page_set import K_DOCS, PageCollector, PageSet
from .publish_list import read_publish_list
from .source_revision import read_head_commit

K_DEFAULT_OUTPUT = Path("build") / "docs" / "bundle"
K_RELEASE = re.compile(r"^\d+\.\d+\.\d+$")
K_MANIFEST_NAME = "bundle.json"
K_STAGING = ".docs-bundle-staging"


@dataclass(frozen=True, slots=True)
class BundleRequest:
    """Holds what to bundle, the release to name it after and where to write it."""

    repository_root: Path
    release: str
    output_dir: Path
    api: ApiSource | None = None


@dataclass(frozen=True, slots=True)
class BundleResult:
    """Holds the archive a run wrote, its SHA-256 and how many pages it carries."""

    archive: Path
    sha256: str
    page_count: int


@final
class BundleProducer:
    """Produces one repository's documentation bundle."""

    def __init__(self, read_commit: Callable[[Path], str] = read_head_commit) -> None:
        """Stores the reader of the commit a bundle records."""
        self._read_commit = read_commit

    def produce(self, request: BundleRequest) -> BundleResult:
        """Writes `docs-bundle-<release>.tar.gz` into the request's output folder.

        Raises:
            DocsBundleError: The release, the publish list, a page or the API reference
                cannot be used; nothing is archived.
        """
        if not K_RELEASE.match(request.release):
            raise ReleaseError(
                f"{request.release!r} is not a release; write it as 1.2.3, without the v of the tag."
            )
        root = request.repository_root
        publish_list = read_publish_list(root / K_DOCS)
        page_set = PageCollector(root, publish_list).collect()
        identity = BundleIdentity(request.release, self._read_commit(root))
        staging = request.output_dir / K_STAGING
        if staging.exists():
            shutil.rmtree(staging)
        self._stage_pages(root, page_set, staging)
        if publish_list.api:
            stage_api(request.api, staging / K_API_ROOT)
        manifest = build_manifest(identity, publish_list, page_set, has_api=publish_list.api)
        text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        (staging / K_MANIFEST_NAME).write_bytes(text.encode("utf-8"))
        archive = request.output_dir / f"docs-bundle-{request.release}.tar.gz"
        digest = write_archive(staging, archive)
        return BundleResult(archive, digest, len(page_set.pages))

    def _stage_pages(self, root: Path, page_set: PageSet, staging: Path) -> None:
        """Copies every published page and asset under the staging folder's pages/."""
        sources = [page.source for page in page_set.pages] + list(page_set.assets)
        for source in sources:
            target = staging / K_PAGES_DIR / source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / K_DOCS / source, target)
