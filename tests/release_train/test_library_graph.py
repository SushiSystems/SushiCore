# test_library_graph.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for reading the pins of a workspace and ordering a train."""

from pathlib import Path

import pytest

from sushicore.files_memory import MemoryFiles
from sushicore.release_train.errors import ReleaseTrainError
from sushicore.release_train.library_graph import K_PINS_FILE, LibraryGraph

pytestmark = pytest.mark.small

K_ROOT = Path("/w")


def _graph(**pins):
    files = MemoryFiles({K_ROOT / name / K_PINS_FILE: "".join(f"[sushisystems.{below}]\nversion = \"v1.0.0\"\n"
                                                              for below in below_list)
                         for name, below_list in pins.items()})
    return LibraryGraph.read(K_ROOT, files)


def test_a_train_takes_every_library_above_and_puts_each_after_what_it_pins():
    graph = _graph(log=[], profiler=[], runtime=["log", "profiler"], blas=["runtime", "log"], dsp=[])
    assert graph.train(["log"]) == ["log", "runtime", "blas"]
    assert graph.train(["profiler", "log"]) == ["log", "profiler", "runtime", "blas"]


def test_an_unknown_library_or_a_cycle_raises():
    with pytest.raises(ReleaseTrainError, match="no library"):
        _graph(log=[]).train(["nothing"])
    with pytest.raises(ReleaseTrainError, match="cycle"):
        _graph(a=["b"], b=["a"]).train(["a"])
