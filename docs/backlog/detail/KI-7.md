# KI-7 A command run outside a checkout prints plain text and no console line

The row of this entry is in `docs/backlog/COMMANDS.md`. This file holds what did not fit the row.

- Origin: own
- Where: `source/sushicore/module_config.py`
- Cause: `find_project_root` raises `SystemExit(message)`
- Recognise: the message reaches stderr without the console's icon or a machine-mode event
- Workaround: run the command inside a checkout
- Fix: RW-26
