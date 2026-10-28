# sushicore.backlog

The backlog of a repository, remaining work and known issues as tables in `docs/backlog/`, and
the `backlog` command group a CLI registers to read and change it. The store, the order and every
command are in [Backlog](../../../docs/reference/BACKLOG.md).

## What it owns

| Name | File | Does |
| --- | --- | --- |
| `BacklogError`, `RowError`, `EntryNotFoundError`, `RefusedChangeError` | `errors.py` | The failures the commands report as one line |
| `WorkEntry`, `IssueEntry` | `model.py` | The two kinds of entry, their columns, their values and one row read or written |
| `BacklogStore`, `BacklogConfig`, `IdLedger`, `Fault` | `store.py` | Read and write the area files, `ids.toml`, `backlog.toml`, the details and the index |
| `next_work`, `decisions`, `is_late` | `order.py` | The age limits and the order of `next` |
| `check_backlog`, `late_entries` | `check.py` | Every rule of `backlog check` |
| `BacklogEditor`, `Closed` | `editor.py` | Add, promote, set, move, close, pin, and the areas |
| `BacklogImporter`, `BacklogRenumberer` | `importer.py` | `import` from the retired files and `renumber` after a merge |
| `register_backlog_commands` | `commands.py` | Add the `backlog` group to a Typer application |
| `main` | `__main__.py` | `python -m sushicore.backlog`, for a repository with no CLI |

## What it depends on

`sushicore.errors`, `sushicore.workspace.read_toml` and `sushicore.citations`. `commands.py`
imports Typer inside `register_backlog_commands`, and reads the open design topics for the
coverage rule from `sushicore.design.store` inside the check command. Inside the package a file
imports only files in a lower layer; `tools/layering/check_package_layers.py` holds the layers.

## Using it

```python
from sushicore.backlog import register_backlog_commands

register_backlog_commands(app, program="se", panel="Project", project_root=find_root)
```
