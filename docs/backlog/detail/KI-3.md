# KI-3 The doctor's `table` event carries Rich markup

The row of this entry is in `docs/backlog/MACHINE_OUTPUT.md`. This file holds what did not fit the row.

- Origin: own
- Where: `source/sushicore/provision/doctor.py`
- Cause: the state cells are written as `[success]ok[/success]` and `[error]FAIL[/error]`
- Recognise: a consumer of the event shows the brackets
- Workaround: strip `[...]` tags in the consumer
- Fix: RW-41
