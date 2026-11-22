# sushicore.docker

The `docker build` and `docker run` of a module's developer image, which the module CLIs with a
`docker` command share. A CLI names its image once and hands its console and runner over; the
commands print a header and one line per choice, and return docker's exit code.

```python
from sushicore.docker import DockerEnvironment, DockerImage

image = DockerImage("sushiengine", "/workspace/sushiengine")
environment = DockerEnvironment(image, root, console, runner)
environment.build(build_args={"SUSHIRUNTIME_REF": "v0.4.0"})
environment.run(gpus=False)
```

## What it owns

| Name | File | Does |
| --- | --- | --- |
| `DockerImage`, `K_DOCKERFILE` | `docker_image.py` | The image tag, the folder the checkout is mounted at, and the Dockerfile, `.config/docker/Dockerfile` by default |
| `DockerConsole` | `docker_console.py` | The four console calls the commands make: `header`, `info`, `success`, `error` |
| `DockerEnvironment`, `K_DEFAULT_COMMAND` | `docker_environment.py` | `build`, which tags the image from the Dockerfile with the repository root as its context, and `run`, which starts an interactive container with the checkout mounted live |

## Building and running

`build` takes `no_cache`, `build_args` for each `--build-arg` and `extra` for any other argument,
and names each choice in a line. A failed build says so and returns docker's code.

`run` passes every GPU through unless `gpus=False`, runs privileged with `SYS_ADMIN` when
`privileged=True`, as a profiler such as perf needs, and starts `/bin/bash` unless `command`
names another program. The checkout is mounted at the image's workdir and the container starts
there, the folder the Dockerfile's `WORKDIR` names too.

## What it depends on

`sushicore.proc.CommandRunner` for the commands. It reads no config: what a CLI configures, such
as the image tag, reaches it through `DockerImage`.
