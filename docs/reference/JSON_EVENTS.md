# JSON events

In machine mode a console writes one JSON object per line to stdout, in UTF-8. A program reads
the stream; the SushiHub desktop application is the reader it was designed for, and its schema
depends on the keys below.

## Turning it on

`build_console(paths, machine=True)` selects `JsonRenderer`. `LazyConsole.machine = True` does
the same for a console built on first use, so a CLI sets it while parsing its command line,
before anything prints. Theme and icons are still loaded.

Of the seven CLIs only `hub` offers the stream, as `--json`.

## The events

The vocabulary is `EVENT_KINDS` in `sushicore/events.py`, and `event_line(kind, **fields)` is
its one serialisation. `event` is always the first key.

```json
{"event": "line",     "level": "info", "message": "..."}
{"event": "command",  "command": "cmake -S . -B build"}
{"event": "header",   "title": "SushiStack Install"}
{"event": "panel",    "title": "...", "body": "..."}
{"event": "table",    "title": "...", "columns": ["A", "B"], "rows": [["a1", "b1"]]}
{"event": "progress", "label": "install-deps", "index": 2, "count": 4, "fraction": 0.5}
{"event": "result",   "ok": true, "payload": {}}
{"event": "prompt",   "id": "prompt-1", "message": "...", "default": "n"}
```

| Event | Notes |
| --- | --- |
| `line` | `level` is one of `info`, `success`, `warn`, `error` |
| `table` | Carries every column and row; `group_by` changes only the terminal |
| `progress` | `fraction` may be `null` |
| `result` | The command's outcome; `payload` is an object, empty when the command gives none |
| `prompt` | `id` is `prompt-N`, counted per console; `default` may be `null` |

The serialisation writes no space after `:` or `,`; the samples above are spaced for reading.

## Prompts

A `prompt` event is answered by one line on stdin. The renderer returns it stripped. An empty
line returns the default, and so does end of input.

## What else reaches the streams

Anything printed through `console.console`, the raw Rich console, goes to stderr without colour.

Three defects break the contract today, and each is listed in
[Known issues](KNOWN_ISSUES.md): the `level` of a `line` event is read from the icon prefix, a
child process inherits stdout, and `doctor` puts Rich markup in its `table` rows.

## Where the design is

The event stream was designed for hub. Sections 4 and 7 of SushiStack's hub design of
2026-09-05, kept in the SushiStack repository, hold the reasoning.
