# Commands

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-142 | P3 | open | Write one gpus slot per accelerator the machine carries, not a fixed one | resources.json holds a slot for each detected accelerator |  | `source/sushicore/testing/accelerator_slots.py` | 2026-11-21 |
| RW-143 | P3 | open | Replace the signature feature detection of run_tests with a declared interface | run_tests asks the module for options through a protocol, not inspect.signature |  | `source/sushicore/testing/session.py` | 2026-11-21 |
| RW-158 | P2 | open | Declare the canonical build, run, bench and check commands, the panels and the verb list | sushicore.command_surface registers build, run, bench and check from a CLI service, with the sanitize option, panels and verb assertion tested |  | `docs/guides/CLI_INTEGRATION.md` | 2026-11-22 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
