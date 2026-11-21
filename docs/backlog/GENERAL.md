# General

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-7 | P2 | open | Decide whether the Windows GPU installer is deleted | `source/sushicore/provision/gpu/windows_installer.py` is deleted, or kept with a caller |  | `docs/design/GPU_TOOLKIT_SELECTION/README.md` | 2026-10-19 |
| RW-137 | P2 | open | Run the pre-commit checks in 8 s: skip the history checkers and split suites by file | The pre-commit run takes under 10 s, CI still runs the history checkers, and nightly fetches the full history |  | `tools/check_all.py` | 2026-11-21 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
