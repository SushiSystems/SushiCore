# Continuous integration

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-50 | P2 | open | Guard the consumer contract before a tag | CI runs the consumer command lines' suites against the package under test, with a token that reads the private ones, before a release is tagged |  |  | 2026-10-19 |
| RW-71 | P2 | open | Add an in-memory package manager so the steps tests drop their two manager stand-ins | tests/provision/test_steps holds no subclass of a package manager |  |  | 2026-11-07 |
| RW-72 | P3 | decision | Decide whether GpuStage and MachineActions leave provision/steps.py, now 940 lines | the owner has ruled and steps.py holds what the ruling leaves in it |  |  | 2026-11-07 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-26 | dependency | A truecolour render after a 256-colour one in one process loses its truecolour codes | Render one colour system per process; tests/conftest.py clears Rich's caches per test | none, Rich caches the downgraded style |  | 2026-11-07 |
