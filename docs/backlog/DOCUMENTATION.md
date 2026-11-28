# Documentation

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-177 | P3 | blocked | Remove check_backlog's open_designs and DesignStore.open_documents | neither name is in the package, and no repository's checker calls them | external: sushiengine and project-mobilerts still carry the copied check_backlog.py that calls both | `source/sushicore/backlog/check.py` | 2026-11-28 |
| RW-178 | P1 | blocked | Move SushiEngine onto sushicore 0.18.1 and close the design-copy entries it holds | SushiEngine's CLI pins sushicore>=0.18.1, its copied check_backlog.py is gone, and the 51 held entries listed in the detail are closed | external: the owner holds SushiEngine while its feature/projectfs_readiness session runs | `source/sushicore/backlog/check.py` | 2026-11-28 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
