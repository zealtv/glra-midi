# cc-easing — glides for CC momentary and CC inc/dec

Suggested model: Sonnet. Build to `docs/config-app.md`.

Bob: "CC momentary (low and high value with easing)", "CC inc or dec with easing".

Engine only, clock injected (`handle(event)` uses the event's `t`;
`tick(now)` returns the messages due; `next_due()` says when to call again, or
`None` when nothing glides):
- A glide moves one (channel, cc) from its current value to a target over the
  event's time along its curve (linear, ease-in, ease-out, ease-in-out), sending
  only when the 7-bit value changes, and ending exactly on the target.
- CC momentary: press glides to high, release glides to low, each from wherever
  the value is at that moment.
- CC step: each press moves the target by the step (clamped 0..127) and glides
  there; presses during a glide retarget it.
- 0 ms means jump, as `layer-engine` left it.
- One glide per (channel, cc); a set-value press or an absolute dial turn on
  the same cc cancels it and wins.
- `release_all()` ends glides in a defined state (the design says which).

Tests with a fake clock: exact value sequences for each curve at a fixed tick,
no duplicate values, retargeting mid-glide, cancel by set/dial, ends on target,
0 ms. No sleeping in tests.
