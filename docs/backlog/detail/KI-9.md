# KI-9 `doctor --for` hides its groups and `--yes` has no `-y`

The row of this entry is in `docs/backlog/COMMANDS.md`. This file holds what did not fit the row.

- Origin: own
- Where: `source/sushicore/provision/commands.py`, `source/sushicore/provision/doctor.py`
- Cause: the help does not list the groups, `infer` and `eval` belong to one module, and the option is declared without its short form
- Recognise: `doctor --help` names no group; `-y` works in `hub` and fails here
- Workaround: read `GROUPS` in `doctor.py`; spell `--yes`
- Fix: RW-6
