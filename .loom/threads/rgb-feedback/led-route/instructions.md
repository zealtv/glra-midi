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
