# test_licence_consent_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A granted consent covers the licences it names and no other."""

from __future__ import annotations

import pytest

from sushicore.provision.licence_consent import Licence, is_accepted
from sushicore.provision.licence_consent_memory import granted_consent

pytestmark = pytest.mark.small

K_ONEAPI = Licence("Intel oneAPI", "https://example.test/oneapi")
K_CUDA = Licence("NVIDIA CUDA", "https://example.test/cuda")


def test_a_granted_consent_accepts_each_licence_it_names():
    """Check that every named licence is accepted."""
    consent = granted_consent(K_ONEAPI, K_CUDA)
    assert is_accepted(consent, K_ONEAPI) and is_accepted(consent, K_CUDA)


def test_a_granted_consent_accepts_no_licence_it_does_not_name():
    """Check that a licence outside the grant is refused."""
    assert not is_accepted(granted_consent(K_ONEAPI), K_CUDA)
