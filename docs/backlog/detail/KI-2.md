# KI-2 With the emoji, minimal or none icons every warning is reported as info

The row of this entry is in `docs/backlog/MACHINE_OUTPUT.md`. This file holds what did not fit the row.

- Origin: own
- Where: `source/sushicore/renderer.py`
- Cause: `_level_from_prefix` reads a JSON `line` event's level from the icon prefix
- Recognise: a warning or an error arrives as `"level": "info"` in machine mode
- Workaround: use the default icon set in machine mode
- Fix: RW-30
