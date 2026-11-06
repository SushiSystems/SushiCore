# Continuous integration

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-50 | P2 | open | Guard the consumer contract before a tag | CI runs the consumer command lines' suites against the package under test, with a token that reads the private ones, before a release is tagged |  |  | 2026-10-19 |
| RW-68 | P3 | blocked | Have SushiSkills drop or relocate the budget-settings checker test that skips outside it | tools/tests/test_test_budget_settings.py no longer skips here or no longer ships to repositories without skills/ | external: the shared tools are owned by SushiSkills |  | 2026-11-07 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
