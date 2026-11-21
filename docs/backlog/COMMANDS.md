# Commands

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-142 | P3 | open | Write one gpus slot per accelerator the machine carries, not a fixed one | resources.json holds a slot for each detected accelerator |  | `source/sushicore/testing/accelerator_slots.py` | 2026-11-21 |
| RW-143 | P3 | open | Replace the signature feature detection of run_tests with a declared interface | run_tests asks the module for options through a protocol, not inspect.signature |  | `source/sushicore/testing/session.py` | 2026-11-21 |
| RW-155 | P2 | open | Keep a rerun that wrote no results from crashing the budget reader | A run whose failed test fails again alone and writes no result file still prints the failing test and the exit code |  | `source/sushicore/testing/budget.py` | 2026-11-22 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
