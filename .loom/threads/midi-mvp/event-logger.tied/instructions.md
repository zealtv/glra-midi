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

## Update 2026-11-12 (orchestrator)
The hard dependency on `unique-assignments` has been removed so the decoder can be built
now. Report formats and real captures are in
`../raw-report-capture.tied/findings.md` and `captures/*.jsonl`. Turn them into
fixtures. Write a **provisional** `device/layout.json` from the stock codes
and Bob's key numbering (findings table). Note that the three dials send identical
codes on stock, so the provisional layout can only say "a dial". Mark
it provisional; `unique-assignments` replaces it. Hardware checks (replug, live
monitor) wait for Bob. `silent-capture` still depends on this stitch.
