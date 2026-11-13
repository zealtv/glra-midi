# Import `hid` on the main thread: its first import on a worker thread crashes the app at exit

When touching `glra_midi/app/padworker.py`, `glra_midi/app/device.py`, `glra_midi/device/backend.py` or anything that calls hidapi from a thread other than the main one, or when a "Python quit unexpectedly" popup follows closing the config app: `import hid` must first run on the main thread.

## Triggers
- hidapi
- import hid
- hid_exit
- IOHIDManagerClose
- Python quit unexpectedly
- EXC_BREAKPOINT
- PadWorker

## Context
As of 2026-11-13 (macOS 14.6.1, Python 3.14, hidapi 0.15.0), `import hid` initialises
hidapi, and on macOS that attaches its IOHIDManager to the run loop of the importing
thread. The `hid` module's exit hook (`hid_exit`) closes the manager from the main thread at
interpreter exit; if the import ran on a thread that has since ended, that close walks a dead
run loop and the process dies with EXC_BREAKPOINT in `CFRunLoopRemoveSource` (Bob's three
reports, 18:11-18:42). `backend.enumerate_devices` and `open_device` import `hid` lazily, so
in the config app the pad worker did the first import.

Reproduced without the pad (`loom:fix-quit-crash`): a bare thread calling `import hid` and
an unfiltered `hid.enumerate()` exits 133 and writes a `Python-*.ips` with Bob's stack; the
same call after a main-thread `import hid` exits 0. A *filtered* `hid.enumerate(VID, PID)`
on a thread with the pad absent did not crash; the real app's quit without the pad did not
either, so the crash needs devices in the manager's set. The fix: `RealPad()` calls
`device.load_hidapi()` on the UI thread; a unit test pins the importing thread with a
stand-in `hid` module. Single-thread paths (`glra-midi run`, `monitor`) import on the main
thread and aren't affected. Not tested with Bob's pad attached.

## Associations
- [[glra-studio-reuse]]
- [[keyboard-seize-needs-root]]
