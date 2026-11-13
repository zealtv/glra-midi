# led-route — choose the lighting route with Bob

**Needs Bob.** Suggested model: Opus.

From `led-probe` findings, pick one and record it in glean:
- **A. Live per-key (RAM):** host owns every LED; all animations are host-driven
  frames at the measured safe rate. Full goal as written.
- **B. Per-key only via flash:** static per-key colours, written rarely (e.g. on
  bank change, rate-limited); animations come from firmware global modes only.
  Rescope `led-animator` and the consumers' expectations with Bob.
- **C. Global only:** bank = global colour/mode; toggle feedback isn't possible
  per key. Rescope with Bob and update `midi-feedback` / `banks` sketches.
Then update the `led-driver`, `led-animator` and `led-demo` instructions to fit
(frame rate, write budget, which features are dropped), before they're claimed.

## Decision (Bob, 2026-11-13): route B

"we'll go B." Per-key colours and firmware modes, written rarely (e.g. on a
bank change), under a write budget; motion comes from the firmware's own modes
(e.g. 11, lit on press). Every lighting write persists to flash at once
(`glean:k16n3-lighting`; `led-probe`, `led-commit-timing`), and no RAM path
exists on stock firmware (`led-ram-path`). Recorded in `glean:k16n3-lighting`.

Still to do in this stitch: set the write budget (rate cap and per-session
count) and rewrite `led-driver`, `led-animator`, `led-demo` and
`led-acceptance` to fit B before they're claimed. Bob still wants to explore
firmware approaches (`loom:firmware-approaches`); that doesn't block B.

## Closed (Bob, 2026-11-13, later the same day)

"for the moment we will accept using the factory firmware led modes and
continue with the app creation" (`lore:2026-11-13-config-app-brief`). The route
decision stands as recorded; the write budget and the rewrite of `led-driver`,
`led-animator`, `led-demo` and `led-acceptance` weren't done, because those
stitches were dropped the same day. Choosing a factory mode moved to
`loom:config-app` (`lighting-modes`, `app-device-panel`).
