# General

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-7 | P2 | open | Decide whether the Windows GPU installer is deleted | `source/sushicore/provision/gpu/windows_installer.py` is deleted, or kept with a caller |  | `docs/design/GPU_TOOLKIT_SELECTION/README.md` | 2026-10-19 |
| RW-136 | P2 | open | Close the pre-commit hook's silent cleanup, untested index path and long lines | A failed cleanup is printed, run() has no mixed jobs, a test covers GIT_INDEX_FILE and no line passes 100 columns |  | `tools/hooks/pre_commit.py` | 2026-11-21 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
