# cc-easing — glides for CC momentary and CC inc/dec

Suggested model: Sonnet. Build to `docs/config-app.md`.

Bob: "CC momentary (low and high value with easing)", "CC inc or dec with easing".

Engine only, clock injected (`handle(event)` uses the event's `t`;
`tick(now)` returns the messages due; `next_due()` says when to call again, or
`None` when nothing glides):
- A glide moves one (channel, cc) from its current value to a target over the
  event's time along its curve (linear, ease-in, ease-out, ease-in-out; the
  quadratic formulas in `docs/config-app.md` §3.6), sending only when the
  7-bit value changes, and ending exactly on the target. Each new target takes
  the full `ease-ms`; tick every 10 ms (100 Hz) while a glide runs.
- CC momentary: press glides to high, release glides to low, each from wherever
  the value is at that moment.
- CC step: each press moves the target by the step (clamped 0..127) and glides
  there; presses during a glide retarget it, building on the old target and
  starting from the current sent value. CC momentary in latch mode toggles
  its target between high and low.
- 0 ms means jump, as `layer-engine` left it.
- One glide per (channel, cc); a set-value press or an absolute dial turn on
  the same cc cancels it and wins.
- `release_all()` per §3.7: held CC momentary jumps to low, every other glide
  jumps to its target.

Tests with a fake clock: exact value sequences for each curve at a fixed tick,
no duplicate values, retargeting mid-glide, cancel by set/dial, ends on target,
0 ms. No sleeping in tests.
