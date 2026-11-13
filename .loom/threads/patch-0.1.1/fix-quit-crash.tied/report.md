# fix-quit-crash — report (worker, 2026-11-13)

## What I built
- `glra_midi/app/device.py`: new `load_hidapi()`, called from `RealPad.__init__`. It does
  `import hid` on the constructing thread, which is the UI thread (`gui.main` → `make_pad`).
  An `ImportError` is swallowed there and left for `RealPad.read` to report as "Pad: not found".
  Nothing in the vendored `glra_midi/device/` changed.
- `tests/test_app_device.py` `HidapiThreadTests` (3 tests, stand-in `hid` module, no real HID):
  `RealPad()` imports `hid` on the calling thread; a later import on another thread finds it
  loaded; a missing module doesn't raise. Two of the three fail with the fix removed.
- `CHANGELOG.md` Fixed line under Unreleased.
- Glean finding `hidapi-main-thread-import` (index regenerated).

## Where it comes from (what I observed)
`import hid` runs hidapi's init, and on macOS that attaches the IOHIDManager to the importing
thread's run loop. `backend.enumerate_devices` / `open_device` import `hid` lazily, so in the
config app the first import ran on the `pad` worker thread (`RealPad.read` via `PadWorker`).
At exit the `hid` module's atexit hook (`hid_exit`) closes the manager on the main thread
against that thread's dead run loop. That matches Bob's stack (`IOHIDManagerClose` ←
`hid_exit` ← `atexit_callfuncs`). The stitch's second option (calling `hid_exit` on the worker)
was not needed.

## How I checked
- Pad not attached during my session (`hid.enumerate(0x36ae, 0x2475)` returned `[]`).
- Reproduced without the pad, outside the app: a script whose only hidapi use was an unfiltered
  `hid.enumerate()` inside a thread exited 133 and macOS wrote `Python-2026-11-13-202327.ips`
  with the same crashed-thread stack as Bob's. The same script with `import hid` on the main
  thread first exited 0. A main-thread *filtered* enumerate also exited 0.
- With the fix: a script mirroring the app (`RealPad()` on main, then unfiltered enumerate on a
  worker thread) exited 0; `glra-midi config --smoke-test` (real app, RealPad, quits itself
  after 1.5 s) exited 0 three times; the `Python-*` report count stayed at 4.
- `./test.sh`: 612 tests OK, before and after merging main.

## What I didn't do / limits
- I couldn't reproduce through the real app: with no pad, `glra-midi config --smoke-test`
  (twice, before the fix) did not crash. A thread-side `hid.enumerate(VID, PID)` with no pad
  also didn't, while the unfiltered one did, so the app crash seems to need the pad (or other
  devices) in the manager's set. So the app-level fix is **checked by the script reproduction,
  the unit tests, and clean smoke runs without the pad, not by quitting the app with the pad
  connected.** Suggest Bob (or a read-only session with the pad plugged in) closes the app once
  and confirms no new `Python-*.ips`.
- The 20:23 `Python-2026-11-13-202327.ips` in `~/Library/Logs/DiagnosticReports/` is from my
  repro script, not the app. I left it.
- `glra-midi run` / `monitor` not run; by reading, they import `hid` on the main thread only.
- No pad writes, no Apply, no lighting changes.

## Open questions
None blocking.
