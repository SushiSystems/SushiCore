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
| `Commit`, `unverified_ids` | `unverified.py` | Judge which IDs the commits after the stamp, with their paths, leave unverified |
| `GitVerification` | `verification.py` | Read the stamp in the git directory and the commits after it with their paths |
| `BacklogEditor`, `Closed` | `editor.py` | Add, promote, set, move, close, pin, and the areas |
| `BacklogRenumberer`, `RenumberResult` | `renumber.py` | `renumber` after a merge: both sides of every conflict, the counters, the index and clashing IDs |
| `CommandContext`, `json_option`, `entry_payload`, `entry_line` | `command_context.py` | The repository, the printing and the unverified mark every command shares |
| `register_list`, `register_show`, `register_next`, `register_decisions`, `register_check` | `command_read.py` | One function per command that reads the store |
| `register_add_work`, `register_close`, `register_renumber` and one for each other command | `command_write.py` | One function per command that changes the store |
| `register_backlog_commands` | `commands.py` | Build the groups and the context, call each command's function, and add the `backlog` group to a Typer application |
| `main` | `__main__.py` | `python -m sushicore.backlog`, for a repository with no CLI |

## What it depends on

`sushicore.errors`, `sushicore.files`, `sushicore.proc` with `sushicore.quiet_runner` for the git
calls of `renumber` and the verification stamp, `sushicore.command_groups` and
`sushicore.renderer`. Each registering function in `command_read.py` and `command_write.py`
imports Typer inside itself, and `command_read.py` reads the open design topics for the coverage
rule from `sushicore.design.store` inside the check command. Inside the package a file
imports only files in a lower layer; `tools/layering/check_package_layers.py` holds the layers.

## Using it

```python
from sushicore.backlog import register_backlog_commands

register_backlog_commands(app, program="se", panel="Project", project_root=find_root)
```
