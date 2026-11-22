# test_docker_image.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Which Dockerfile an image is built from."""

from pathlib import Path

import pytest

from sushicore.docker import DockerImage

pytestmark = pytest.mark.small


def test_an_image_is_built_from_the_dockerfile_every_module_keeps_unless_told_otherwise():
    assert Path(DockerImage("sushiruntime", "/workspace/sushiruntime").dockerfile) == Path(
        ".config", "docker", "Dockerfile")
    assert DockerImage("x", "/w", dockerfile="docker/Dockerfile").dockerfile == "docker/Dockerfile"
