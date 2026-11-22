# docker_image.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Names a module's developer image: its tag, its Dockerfile and where the checkout is mounted."""

from __future__ import annotations

from dataclasses import dataclass

#: The Dockerfile of every Sushi module, from the repository root; its ignore file sits beside it.
K_DOCKERFILE = ".config/docker/Dockerfile"


@dataclass(frozen=True, slots=True)
class DockerImage:
    """The developer image of one module.

    Args:
        name: The image tag, such as ``sushiengine``.
        workdir: The folder in the container the checkout is mounted at and a shell starts in,
            such as ``/workspace/sushiengine``; the Dockerfile's ``WORKDIR`` names the same one.
        dockerfile: The Dockerfile, relative to the repository root.
    """

    name: str
    workdir: str
    dockerfile: str = K_DOCKERFILE
