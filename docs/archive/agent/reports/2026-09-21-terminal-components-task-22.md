# Task 22: virtual terminal processing in a Windows console

## Files changed

- `sushicore/windows_console.py` (new): `enable_virtual_terminal(kernel32=None)` and `default_kernel32()`, plus the private `_turn_on`.
- `sushicore/renderer.py`: `RichRenderer.__init__` imports `enable_virtual_terminal` inside the method and calls it after `_force_utf8_streams()` and before it builds the Rich console.
- `tests/test_windows_console.py` (new): eight tests against a recording fake `kernel32`, one Windows-only test of the default prototypes.
- `tests/test_renderer_components.py`: a helper for the subprocess check, the existing Rich test kept under its name, a sibling test for `sushicore.windows_console`, a test that a `RichRenderer` calls the switch once, and an autouse fixture that replaces the switch with a no-op.

## Red first

Before `windows_console.py` existed:

```
ImportError while importing test module 'D:\Projects\sushicore\tests\test_windows_console.py'.
E   ImportError: cannot import name 'windows_console' from 'sushicore' (D:\Projects\sushicore\sushicore\__init__.py)
1 error in 0.15s
```

With the module in place and the renderer's call temporarily replaced by a bare reference (restored afterwards):

```
>       assert calls == [1]
E       assert [] == [1]
FAILED tests/test_renderer_components.py::test_constructing_a_rich_renderer_switches_on_virtual_terminal_processing_once
1 failed, 9 passed in 0.23s
```

## Green

```
$ PYTHONPATH=D:/Projects/sushicore python -m pytest tests/test_windows_console.py tests/test_renderer_components.py -q
...................                                                      [100%]
19 passed in 0.20s
```

Syntax check:

```
$ python -m py_compile sushicore/windows_console.py sushicore/renderer.py tests/test_windows_console.py tests/test_renderer_components.py; echo "exit $?"
exit 0
```

Both orders (Task 23's files were not failing at the time):

```
$ python -m pytest tests -q
387 passed in 1.07s
$ python -m pytest $(ls tests/test_*.py | sort -r) tests/ui tests/help -q
387 passed in 1.01s
```

No line in the four files is over 100 columns (`awk 'length>100'` printed nothing).

## The 64-bit handle check

`default_kernel32()` sets `GetStdHandle.restype = wintypes.HANDLE` and `argtypes = [wintypes.DWORD]`. `GetConsoleMode` takes `[HANDLE, POINTER(DWORD)]` and `SetConsoleMode` takes `[HANDLE, DWORD]`, both returning `BOOL`. All of it happens inside the function, none at import. A Windows-only test reads those prototypes and asserts the handle type is pointer-wide; it calls no Win32 function.

An ad-hoc script (not a test) on this machine, Python 3.13, 64-bit:

```
restype: <class 'ctypes.c_void_p'> sizeof: 8
GetStdHandle(-11): int 768
get_osfhandle(1) : 768
equal: True
GetCurrentProcess default c_int: -1
GetCurrentProcess HANDLE     : 0xffffffffffffffff
```

`GetStdHandle(-11)` matches the C runtime's handle for fd 1. Real console handles are small numbers, so they never show truncation; the pseudo handle of `GetCurrentProcess` (all bits set) shows the default `c_int` return type reading it as `-1` and the `HANDLE` type reading it whole. That script called the real `GetStdHandle` and `GetCurrentProcess`, both read-only; it did not call `GetConsoleMode` or `SetConsoleMode`.

## Choices to know about

- The default `kernel32` is `ctypes.WinDLL("kernel32", use_last_error=True)`, not `ctypes.windll.kernel32` as the plan says. `windll.kernel32` is shared, and its function objects carry the prototypes other libraries (Rich) already set on them; a private `WinDLL` has its own function objects, so setting prototypes cannot collide.
- The mode buffer is a `wintypes.DWORD` passed as `ctypes.pointer(...)`. The fake reads and writes it through `pointer.contents.value`.
- `_turn_on` and `default_kernel32` import `ctypes.wintypes` locally, after the platform check, so the module loads on every platform.
- An API error on the second handle after the first was written returns `False`, as the plan words it ("any `OSError` or `AttributeError` ... the result is `False`").

## Not done

- Tests in other files that build a `RichRenderer` (for example through `Console`) still reach the real `enable_virtual_terminal`, because `tests/conftest.py` is outside my file list. Under pytest's default capture, stdout and stderr are not consoles, so `GetConsoleMode` fails and nothing is written. Running with `-s` in a real console would switch VT on for that window. An autouse no-op in `conftest.py` would close it; the orchestrator can decide. `tests/test_renderer_components.py` carries its own autouse no-op.
- The real function was never run against a real console.
- No docs, changelog, `__init__.py` or `pyproject.toml` edits, no commit.
