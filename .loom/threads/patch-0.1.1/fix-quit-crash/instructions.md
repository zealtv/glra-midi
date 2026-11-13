# fix-quit-crash — "Python quit unexpectedly" when closing the app

Bob, 2026-11-13: "i get a python quit unexpectedly popup upon closing the app."
macOS kept three reports (18:11, 18:14, 18:42); one is in `../evidence/`. All
show the same main-thread stack: EXC_BREAKPOINT in `CFRunLoopRemoveSource` ←
`IOHIDDeviceUnscheduleFromRunLoop` ← `IOHIDManagerClose` ← hidapi's `hid_exit`,
called from Python at interpreter exit.

Claude's reading (2026-11-13, from the stack): hidapi's IOHIDManager got
scheduled on the pad worker thread's run loop (first HID call there), and the
`hid` module's exit hook closes it from the main thread after that thread and
its run loop are gone. Options to test: make the first hidapi call (init or
enumerate) on the main thread before the worker starts; or call `hid_exit` on
the worker thread in `PadWorker.shutdown` before the thread ends. Check
whether `glra-midi run`/`monitor` (single thread) are unaffected. Verify by
quitting the real app with the pad connected (Bob, or a read-only session:
opening and closing the app does no writes) and checking no new
`Python-*.ips` appears in `~/Library/Logs/DiagnosticReports/`.
