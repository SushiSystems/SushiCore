# Releases

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-106 | P1 | open | Drop SushiStack's import of the deleted gh_latest helpers before it takes this SushiCore | sushistack cli/sushihub/setup/package_managers.py imports no gh_latest name and its suite passes on this SushiCore |  | `source/sushicore/provision/packages/github_release.py` | 2026-11-17 |
| RW-117 | P1 | open | Move SushiRuntime's CLI off the deprecated package_install command helpers | sushiruntime cli imports no CapturedRun, capture_command or run_command from package_install and its suite passes |  | `source/sushicore/provision/captured_run.py` | 2026-11-17 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
