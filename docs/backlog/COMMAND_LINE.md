# Command line

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-37 | P2 | open | End every provisioning command with one `result` event | `setup`, `link` and `unlink` emit `result` through one exit helper (Cli C5) |  |  | 2026-10-19 |
| RW-39 | P2 | open | Validate the workspace before `link` writes | `link --workspace` refuses a path without the workspace marker, and the module pointer and the `[modules]` entry are written as one operation (Cli C12) |  |  | 2026-10-19 |
| RW-41 | P2 | open | Keep markup out of the doctor's `table` event | the rows of the `table` event carry plain text (Cli C2) |  |  | 2026-10-19 |
| RW-42 | P2 | open | Report the file a configuration value came from | `config` names `config.local.toml` or the linked workspace when a value came from there (Cli C20) |  |  | 2026-10-19 |
| RW-52 | P2 | open | Take a theme from a file as well as a directory | `LazyConsole` reads a `[cli]` theme from a file it is given, such as a workspace's `workspace.toml` |  |  | 2026-10-19 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
