@AGENTS.md

## Backlog and design

1. Session start: `python -m sushicore.backlog next`. Take what it gives.
2. A defect or limitation turns up: `python -m sushicore.backlog add issue ...` or `python -m sushicore.backlog add work ...`
   at once.
3. Before changing a module: `python -m sushicore.design owner <path>`.
4. Finishing: `python -m sushicore.backlog close <ID>` in the same commit, and the changelog line it prints.
   The commit message ends with `Backlog: <ID>`, or `Backlog: none (<reason>)`.
5. Once per clone: `python tools/hooks/install_hooks.py`.

State is read with these commands. It is never read from a markdown file or the git log.
