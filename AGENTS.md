# Agent instructions

SushiCore is the Python package behind the command lines of the Sushi stack: workspace resolution,
layered configuration, the console, the CMake driver and dependency provisioning. It has no program of
its own beyond the three modules it runs with `python -m`: `sushicore.backlog`, `sushicore.design` and
`sushicore.docs_bundle`.

Load `sushiskills` before working here; it names the skill each task needs. This repository follows
`python-code-style`, `testing`, `documentation`, `backlog`, `design`, `commits` and `source-comments`.

## Commands

```
python -m pytest                          the tests; small and medium run anywhere
python -m sushicore.tools check .         every checker and the repository's own tests
python -m sushicore.backlog next          what to do next
python -m sushicore.design owner <path>   which design topic owns a path
python -m sushicore.tools install-hooks . once per clone, so git runs the checks before a commit
```

A build tool of another repository is never run from here; a repository is built through its own
command line.

## Folders

| Path | Holds |
| --- | --- |
| `source/sushicore/` | The package; `provision/` is the dependency provisioning, `backlog/`, `design/` and `docs_bundle/` are the documentation tools |
| `tests/` | A tree that mirrors the source, one test file per source file |
| `source/sushicore/tools/` | The checkers every Sushi repository runs, `python -m sushicore.tools`; `layering/check_package_layers.py` holds the layer table of each package |
| `tools/` | This repository's settings, known findings and git hooks for those checkers |
| `docs/` | The manual, the backlog, the design topics and the work folders |

The layout is the single-package Python layout of `python-code-style`: `pyproject.toml` at the root, the package
under `source/` and the tests in `tests/`. The package supports Python 3.10 and later, and the tests run on 3.10 and 3.11.

Every public name the manual describes is changed with its page in the same commit.
