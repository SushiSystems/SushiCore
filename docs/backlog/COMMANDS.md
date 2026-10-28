# Commands

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-7 | own | A command run outside a checkout prints plain text and no console line | run the command inside a checkout | RW-26 |  | 2026-10-19 |
| KI-8 | own | `link` registers a workspace that is not one and can leave half a link | give `--workspace` a real workspace root; run `unlink` after a failure | RW-39 |  | 2026-10-19 |
| KI-9 | own | `doctor --for` hides its groups and `--yes` has no `-y` | read `GROUPS` in `doctor.py`; spell `--yes` | RW-6 |  | 2026-10-19 |
| KI-10 | own | The provisioning commands assume a `cli/` folder and the `hub` program | keep the command line in `cli/` | RW-25 |  | 2026-10-19 |
| KI-12 | own | `clean` says "removed" when the build tree is still there | close the program holding the file and clean again | RW-43 |  | 2026-10-19 |
| KI-13 | own | An unknown `color` or `background` falls back in silence | check the spelling against the manual | RW-5 |  | 2026-10-19 |
