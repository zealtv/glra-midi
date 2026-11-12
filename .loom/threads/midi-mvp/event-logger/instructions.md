# event-logger — decode the pad into logical events

Suggested model: Sonnet (Opus if the captures show messy edge cases).

The brief's Phase 1 logger, minus the suppression (that's `silent-capture`).
`glra-osc monitor`:
- Finds the pad (VID 36ae / PID 2475), opens the input interface(s) found in
  `raw-report-capture`, and reads reports on a background thread or callback.
- Decodes them via `device/layout.json` into one internal event type, e.g.
  `ControlEvent(control="key.7"|"enc.2", action="down"|"up"|"cw"|"ccw", t)`.
  Encoder push = `enc.N.push` down/up. Report press/release only where the
  hardware really sends it, and say so plainly where it doesn't.
- Prints timestamped lines (`[12:01:03.122] KEY 07 DOWN`); `--raw` adds hex.
- Handles unplug/replug without crashing, and closes cleanly on Ctrl-C.
- Decoder covered by unit tests built on the captured fixtures. Keep the
  decoder pure: bytes in, events out.
