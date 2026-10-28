# KI-5 `setup`, `link` and `unlink` end without a `result` event

The row of this entry is in `docs/backlog/MACHINE_OUTPUT.md`. This file holds what did not fit the row.

- Origin: own
- Where: `source/sushicore/provision/commands.py`
- Cause: no exit helper emits it
- Recognise: the last event of the run is not `result`
- Workaround: read the exit code
- Fix: RW-37
