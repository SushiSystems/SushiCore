# Commands

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-142 | P3 | open | Write one gpus slot per accelerator the machine carries, not a fixed one | resources.json holds a slot for each detected accelerator |  | `source/sushicore/testing/accelerator_slots.py` | 2026-11-21 |
| RW-143 | P3 | open | Replace the signature feature detection of run_tests with a declared interface | run_tests asks the module for options through a protocol, not inspect.signature |  | `source/sushicore/testing/session.py` | 2026-11-21 |
| RW-159 | P2 | open | Declare --report on build and --type on run in the shared command surface | build takes --report and run takes --type, tested and documented |  | `source/sushicore/command_surface/run_command.py` | 2026-11-22 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
