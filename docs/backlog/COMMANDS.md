# Commands

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-59 | P3 | open | Show committed but unbuilt work as unverified when reading the backlog | backlog list and next mark such an entry unverified, a derived state that is never stored |  |  | 2026-10-30 |
| RW-60 | P2 | open | Let the CMake driver write a CTest JUnit file | ctest_run takes output_junit, passes --output-junit to CTest, and a test shows the argument and its absence |  | `source/sushicore/cmake_driver.py` | 2026-10-30 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-7 | own | A command run outside a checkout prints plain text and no console line | run the command inside a checkout | RW-26 |  | 2026-10-19 |
