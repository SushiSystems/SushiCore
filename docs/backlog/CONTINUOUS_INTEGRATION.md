# Continuous integration

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-50 | P2 | open | Guard the consumer contract before a tag | CI runs the consumer command lines' suites against the package under test, with a token that reads the private ones, before a release is tagged |  |  | 2026-10-19 |
| RW-150 | P1 | open | Hash the shared tools in the lock with CRLF read as LF so every checkout matches | A repository with core.autocrlf passes check_shared_tools on its disk, in its index and on Linux |  | `source/sushicore/shared_tools/lock_file.py` | 2026-11-21 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-26 | dependency | A truecolour render after a 256-colour one in one process loses its truecolour codes | Render one colour system per process; tests/conftest.py clears Rich's caches per test | none, Rich caches the downgraded style |  | 2026-11-07 |
