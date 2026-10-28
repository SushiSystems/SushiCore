# KI-4 In machine mode stdout carries a child process's output

The row of this entry is in `docs/backlog/MACHINE_OUTPUT.md`. This file holds what did not fit the row.

- Origin: own
- Where: `source/sushicore/proc.py`, `source/sushicore/provision/steps.py`, `source/sushicore/provision/system.py`, `source/sushicore/provision/toolchains/oneapi.py`
- Cause: `Runner.run` and the provisioning steps let the child inherit stdout
- Recognise: lines that are not JSON events among the events
- Workaround: skip lines that do not parse as JSON
- Fix: RW-27
