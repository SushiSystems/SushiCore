# Commands

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-57 | P2 | open | Export the names of the command groups so repositories stop listing them in tests | a repository surface test reads the group names from sushicore, and DSP and Track tests carry no list |  |  | 2026-10-30 |
| RW-58 | P2 | open | Give repositories one shared helper for the command surface test | a helper in sushicore checks a CLI exposes the groups it should, and two repositories use it |  |  | 2026-10-30 |
| RW-59 | P3 | open | Show committed but unbuilt work as unverified when reading the backlog | backlog list and next mark such an entry unverified, a derived state that is never stored |  |  | 2026-10-30 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-7 | own | A command run outside a checkout prints plain text and no console line | run the command inside a checkout | RW-26 |  | 2026-10-19 |
| KI-9 | own | `doctor --for` hides its groups and `--yes` has no `-y` | read `GROUPS` in `doctor.py`; spell `--yes` | RW-6 |  | 2026-10-19 |
| KI-10 | own | The provisioning commands assume a `cli/` folder and the `hub` program | keep the command line in `cli/` | RW-25 |  | 2026-10-19 |
