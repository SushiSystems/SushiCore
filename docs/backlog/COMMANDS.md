# Commands

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-59 | P3 | open | Show committed but unbuilt work as unverified when reading the backlog | backlog list and next mark such an entry unverified, a derived state that is never stored |  | `docs/design/BACKLOG/README.md` | 2026-10-30 |
| RW-76 | P3 | open | Skip a program whose cases the filter cannot reach in a filtered shard run | sp test -f Small_Json* launches only programs that hold a matching case |  |  | 2026-11-10 |
| RW-86 | P2 | open | Write the shared rows of tools/README.md in shared_tools sync | sync writes the rows of the shared tools into a repository's tools/README.md and keeps the rows of its own tools |  |  | 2026-11-16 |
| RW-87 | P2 | open | Name each setting the synced tools read that tools/settings.py lacks | sync names each K_ setting the copied tools import that the target's tools/settings.py does not define, with SushiCore's value |  |  | 2026-11-16 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-7 | own | A command run outside a checkout prints plain text and no console line | run the command inside a checkout | RW-26 |  | 2026-10-19 |
| KI-32 | own | design show crashes with UnicodeEncodeError on a cp1252 console on an arrow | set PYTHONIOENCODING=utf-8 | none, not yet scheduled |  | 2026-11-16 |
| KI-33 | own | shared_tools sync calls an old SushiSkills copy a local edit | check the file against SushiSkills history, then pass --force | none, the SushiSkills history ends with this move |  | 2026-11-16 |
