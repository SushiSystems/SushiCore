# Commands

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-59 | P3 | open | Show committed but unbuilt work as unverified when reading the backlog | backlog list and next mark such an entry unverified, a derived state that is never stored |  |  | 2026-10-30 |
| RW-76 | P3 | open | Skip a program whose cases the filter cannot reach in a filtered shard run | sp test -f Small_Json* launches only programs that hold a matching case |  |  | 2026-11-10 |
| RW-78 | P1 | open | Gate the test command on the budget and share devices through resource groups | test exits non-zero on a budget finding of a current tree and passes a resource spec to CTest |  |  | 2026-11-11 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-7 | own | A command run outside a checkout prints plain text and no console line | run the command inside a checkout | RW-26 |  | 2026-10-19 |
