# sushicore.design

The design topics of a repository, one topic per subject and one owner per module, and the
`design` command group a CLI registers to open, check and merge them. The frame, the ownership
rule and every command are in [Design topics](../../../docs/reference/DESIGN.md).

## What it owns

| Name | File | Does |
| --- | --- | --- |
| `DesignError`, `TopicNotFoundError`, `OwnedModuleError` | `errors.py` | The failures the commands report as one line |
| `TopicDocument`, `Phase`, `parse_topic` | `model.py` | A topic's frame read, written and replaced part by part |
| `DesignStore`, `Topic` | `store.py` | The topics, which topic owns a module, and a new topic, page or phase |
| `check_design`, `Finding` | `check.py` | Every rule of `design check` |
| `find_overlap`, `TopicMerger`, `Overlap`, `MergeResult` | `merge.py` | `overlap` and `merge` |
| `register_design_commands` | `commands.py` | Add the `design` group to a Typer application |
| `main` | `__main__.py` | `python -m sushicore.design`, for a repository with no CLI |

## What it depends on

`sushicore.errors` and `sushicore.citations`. Nothing in `sushicore.backlog`. `commands.py`
imports Typer inside `register_design_commands`. Inside the package a file imports only files in
a lower layer; `tools/layering/check_package_layers.py` holds the layers.

## Using it

```python
from sushicore.design import register_design_commands

register_design_commands(app, program="sr", panel="Project", project_root=find_root)
```
