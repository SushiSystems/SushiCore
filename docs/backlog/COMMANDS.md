# Commands

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-142 | P3 | open | Write one gpus slot per accelerator the machine carries, not a fixed one | resources.json holds a slot for each detected accelerator |  | `source/sushicore/testing/accelerator_slots.py` | 2026-11-21 |
| RW-143 | P3 | open | Replace the signature feature detection of run_tests with a declared interface | run_tests asks the module for options through a protocol, not inspect.signature |  | `source/sushicore/testing/session.py` | 2026-11-21 |
| RW-157 | P2 | open | Ship the shared CMake build policy and the CLI helpers every Sushi C++ repository copies | include(SushiBuild) reaches every shared CMake function and the run-dir, selection and docker helpers have tests |  |  | 2026-11-22 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
