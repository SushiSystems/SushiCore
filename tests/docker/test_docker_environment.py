# test_docker_environment.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The docker command lines a module's developer image is built and run with."""

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.docker import DockerEnvironment, DockerImage
from sushicore.proc_memory import RecordingRunner

pytestmark = pytest.mark.small

K_ROOT = Path("/src/sushiengine")
K_IMAGE = DockerImage("sushiengine", "/workspace/sushiengine")


def _environment(console=None):
    """Return an environment over a recording runner, and the runner."""
    console = console or RecordingConsole()
    runner = RecordingRunner(RecordingConsole())
    return DockerEnvironment(K_IMAGE, K_ROOT, console, runner), runner


def test_build_tags_the_image_from_the_dockerfile_with_the_root_as_context():
    environment, runner = _environment()
    assert environment.build() == 0
    command = runner.commands[0]
    assert list(command.argv) == ["docker", "build", "-f", str(K_ROOT / ".config/docker/Dockerfile"),
                                  "-t", "sushiengine", "."]
    assert command.cwd == K_ROOT


def test_build_passes_no_cache_build_args_and_extra_arguments_before_the_context():
    environment, runner = _environment()
    environment.build(no_cache=True, build_args={"SUSHIRUNTIME_REF": "v1.2.3"}, extra=("--pull",))
    assert list(runner.commands[0].argv)[6:] == [
        "--no-cache", "--build-arg", "SUSHIRUNTIME_REF=v1.2.3", "--pull", "."]


def test_a_failed_build_returns_dockers_code_and_says_so():
    environment, runner = _environment(console := RecordingConsole())
    runner.script(exit_code=3)
    assert environment.build() == 3
    assert console.texts("error") == ["Docker build failed."]


def test_run_mounts_the_checkout_at_the_workdir_with_every_gpu_and_starts_a_shell():
    environment, runner = _environment()
    environment.run()
    assert list(runner.commands[0].argv) == [
        "docker", "run", "-it", "--rm", "--gpus", "all",
        "-v", f"{K_ROOT}:/workspace/sushiengine", "-w", "/workspace/sushiengine",
        "sushiengine", "/bin/bash"]


def test_run_without_gpus_privileged_runs_the_command_named():
    environment, runner = _environment()
    environment.run(gpus=False, privileged=True, command=("perf", "top"), extra=("--net=host",))
    assert list(runner.commands[0].argv) == [
        "docker", "run", "-it", "--rm", "--privileged", "--cap-add=SYS_ADMIN",
        "-v", f"{K_ROOT}:/workspace/sushiengine", "-w", "/workspace/sushiengine",
        "--net=host", "sushiengine", "perf", "top"]
