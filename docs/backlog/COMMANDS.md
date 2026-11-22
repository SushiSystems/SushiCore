# Commands

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-142 | P3 | open | Write one gpus slot per accelerator the machine carries, not a fixed one | resources.json holds a slot for each detected accelerator |  | `source/sushicore/testing/accelerator_slots.py` | 2026-11-21 |
| RW-143 | P3 | open | Replace the signature feature detection of run_tests with a declared interface | run_tests asks the module for options through a protocol, not inspect.signature |  | `source/sushicore/testing/session.py` | 2026-11-21 |
| RW-162 | P2 | open | Let a program inside a tree link the tier module archives instead of the tier libraries | A target sushi_tier_archives() marks links every tier module it reaches as a whole archive and no tier library; SushiEngine's tests and probes do. |  | `source/sushicore/cmake/SushiTierLibraries.cmake` | 2026-11-22 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
