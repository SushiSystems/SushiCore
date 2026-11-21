# Continuous integration

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-50 | P2 | open | Guard the consumer contract before a tag | CI runs the consumer command lines' suites against the package under test, with a token that reads the private ones, before a release is tagged |  |  | 2026-10-19 |
| RW-151 | P1 | open | Show a finding below a submodule link as a path below the root so known findings match | A repository with submodules commits through the index hook with its known findings matched |  | `tools/checking/checker.py` | 2026-11-21 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-26 | dependency | A truecolour render after a 256-colour one in one process loses its truecolour codes | Render one colour system per process; tests/conftest.py clears Rich's caches per test | none, Rich caches the downgraded style |  | 2026-11-07 |
