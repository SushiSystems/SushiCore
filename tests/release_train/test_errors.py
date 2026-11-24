# test_errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the errors of the release train."""

import pytest

from sushicore.errors import SushiCoreError
from sushicore.release_train.errors import ReleaseTrainError

pytestmark = pytest.mark.small


def test_a_train_error_is_a_sushicore_error():
    assert issubclass(ReleaseTrainError, SushiCoreError)
