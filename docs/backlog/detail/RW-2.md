# RW-2 Choose a Python-library exception to the layout, or move to it

The row of this entry is in `docs/backlog/GENERAL.md`. This file holds what did not fit the row.

- State: decision
- Done when: the layout rule names an exception for a Python library, or `pyproject.toml`, the package and `tests/` follow the rule (Lay L13, Lay L18)
- Where: `pyproject.toml`

`pyproject.toml` sits in the repository root. The layout rule forbids the file in the root. Cause:
the package was laid out as a Python library before the layout rule.
