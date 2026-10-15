# test_errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the errors a documentation bundle reports."""

from pathlib import Path

import pytest

from sushicore.docs_bundle.errors import (
    ApiReferenceError,
    DocsBundleError,
    PageError,
    PublishListError,
    ReleaseError,
)
from sushicore.errors import SushiCoreError

pytestmark = pytest.mark.small


@pytest.mark.parametrize("kind", [PublishListError, ApiReferenceError, ReleaseError])
def test_every_bundle_error_is_a_sushicore_error(kind):
    assert issubclass(kind, DocsBundleError)
    assert issubclass(kind, SushiCoreError)


def test_a_page_error_puts_its_location_in_front():
    error = PageError(Path("docs/A.md"), 7, "no title")
    assert str(error) == f"{Path('docs/A.md')}:7: no title"
    assert (error.path, error.line) == (Path("docs/A.md"), 7)
