# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the provisioning file lock."""

from __future__ import annotations

import os

import pytest

from sushicore.provision.lock import LockTimeout, ProvisionLock


def test_lock_is_released_on_exit(tmp_path):
    path = tmp_path / ".lock"
    with ProvisionLock(path):
        pass
    with ProvisionLock(path, timeout=0.5):
        pass


def test_second_holder_times_out_naming_the_pid(tmp_path):
    path = tmp_path / ".lock"
    with ProvisionLock(path):
        with pytest.raises(LockTimeout, match=str(os.getpid())):
            with ProvisionLock(path, timeout=0.3):
                pass
