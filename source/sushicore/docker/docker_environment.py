# docker_environment.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Builds a module's developer image and runs its container with the checkout mounted live."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import final

from ..proc import CommandRunner
from .docker_console import DockerConsole
from .docker_image import DockerImage

#: The shell a container starts when the caller names no command.
K_DEFAULT_COMMAND = ("/bin/bash",)


@final
class DockerEnvironment:
    """The ``docker build`` and ``docker run`` commands of one module's developer image.

    Args:
        image: The image to build and run.
        root: The repository root: the build context, and the folder mounted into the container.
        console: The console each command prints through.
        runner: The runner each docker command runs through.
    """

    def __init__(self, image: DockerImage, root: Path, console: DockerConsole,
                 runner: CommandRunner) -> None:
        """Keep the image, the root, the console and the runner."""
        self._image = image
        self._root = root
        self._console = console
        self._runner = runner

    def build(self, *, no_cache: bool = False, build_args: Mapping[str, str] | None = None,
              extra: Sequence[str] = ()) -> int:
        """Build the image from the repository root and return docker's exit code.

        Args:
            no_cache: Rebuild every layer, ignoring the layer cache.
            build_args: The ``--build-arg`` values, such as ``SUSHIRUNTIME_REF``; each is named in a line.
            extra: Further ``docker build`` arguments, passed before the context.
        """
        self._console.header("Docker build")
        command = ["docker", "build", "-f", str(self._root / self._image.dockerfile),
                   "-t", self._image.name]
        if no_cache:
            self._console.info("Rebuilding every layer (--no-cache).")
            command.append("--no-cache")
        for name, value in (build_args or {}).items():
            self._console.info(f"Building with {name}={value}.")
            command += ["--build-arg", f"{name}={value}"]
        command += [*extra, "."]
        code = self._runner.run(command, self._root)
        if code != 0:
            self._console.error("Docker build failed.")
            return code
        self._console.success(f"Image '{self._image.name}' built.")
        return 0

    def run(self, *, gpus: bool = True, privileged: bool = False,
            command: Sequence[str] = K_DEFAULT_COMMAND, extra: Sequence[str] = ()) -> int:
        """Start an interactive container with the checkout mounted live and return its exit code.

        Args:
            gpus: Pass every GPU through; without them the CPU SYCL device still works.
            privileged: Run privileged with ``SYS_ADMIN``, as a profiler such as perf needs.
            command: What the container runs; a shell by default.
            extra: Further ``docker run`` arguments, passed before the image.
        """
        self._console.header("Docker run")
        argv = ["docker", "run", "-it", "--rm"]
        if gpus:
            argv += ["--gpus", "all"]
        else:
            self._console.info("Running without GPU passthrough.")
        if privileged:
            self._console.info("Running privileged, with SYS_ADMIN.")
            argv += ["--privileged", "--cap-add=SYS_ADMIN"]
        argv += ["-v", f"{self._root}:{self._image.workdir}", "-w", self._image.workdir,
                 *extra, self._image.name, *command]
        return self._runner.run(argv, self._root)
