# Continuous integration

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-50 | P2 | open | Guard the consumer contract before a tag | CI runs the consumer command lines' suites against the package under test, with a token that reads the private ones, before a release is tagged |  |  | 2026-10-19 |
| RW-149 | P1 | open | Let the pre-commit hook check a checkout with autocrlf and submodules as the disk has them | A repository with core.autocrlf and submodules commits through the index hook with the checkers green |  | `tools/hooks/pre_commit.py` | 2026-11-21 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-26 | dependency | A truecolour render after a 256-colour one in one process loses its truecolour codes | Render one colour system per process; tests/conftest.py clears Rich's caches per test | none, Rich caches the downgraded style |  | 2026-11-07 |
