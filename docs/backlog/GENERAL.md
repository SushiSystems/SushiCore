# General

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-7 | P2 | open | Decide whether the Windows GPU installer is deleted | `source/sushicore/provision/gpu/windows_installer.py` is deleted, or kept with a caller |  | `docs/design/GPU_TOOLKIT_SELECTION/README.md` | 2026-10-19 |
| RW-138 | P2 | open | Read the tag's tools with one git call in sync, not one per file | sync asks git once for the tag's files, and the full pytest run does not time out |  | `source/sushicore/shared_tools/git_reader.py` | 2026-11-21 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
