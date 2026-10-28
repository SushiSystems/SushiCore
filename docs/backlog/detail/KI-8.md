# KI-8 `link` registers a workspace that is not one and can leave half a link

The row of this entry is in `docs/backlog/COMMANDS.md`. This file holds what did not fit the row.

- Origin: own
- Where: `source/sushicore/provision/commands.py`
- Cause: `--workspace PATH` is taken unchecked, and the module pointer is written before the workspace's `[modules]` table without undo
- Recognise: a new `.sushistack/workspace.toml` under the path given, or a pointer with no `[modules]` entry after a failed run
- Workaround: give `--workspace` a real workspace root; run `unlink` after a failure
- Fix: RW-39
