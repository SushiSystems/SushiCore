# test_ports.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that each real seam of the train offers every operation its port names."""

import inspect

import pytest

from sushicore.release_train.gh_forge import GhForge
from sushicore.release_train.git_cli import GitCli
from sushicore.release_train.ports import IForge, IGit, IPackageIndex
from sushicore.release_train.pypi_index import PyPiIndex

pytestmark = pytest.mark.small


def _operations(port):
    return {name for name, member in vars(port).items() if inspect.isfunction(member) and not name.startswith("_")}


@pytest.mark.parametrize(("port", "real"), [(IGit, GitCli), (IForge, GhForge), (IPackageIndex, PyPiIndex)])
def test_the_real_seam_offers_each_operation_of_its_port(port, real):
    operations = _operations(port)
    assert operations
    assert operations <= {name for name in dir(real) if callable(getattr(real, name))}
