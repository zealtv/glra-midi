# led-animator — per-key and whole-pad animations, host-side

Suggested model: Sonnet.

A pure, clock-injected engine that produces 16-key frames for `led-driver`:
- A **base layer**: each key's steady colour (what `midi-feedback`/`banks` set).
- **Per-key animations** over the base: e.g. blink, pulse, flash-on-press decay.
- **Whole-pad animations**: e.g. wave/sweep, a short bank-change splash, then
  return to the base layer.
- Layers composite in a defined order; animations end or loop; a frame is only
  emitted when it changes, at no more than the route's frame rate.
- A small API the consumers call: `set_base(key, rgb)`, `animate(key, name, …)`,
  `animate_all(name, …)`, `clear(key)`.
If `led-route` chose B or C, implement only what that route allows (see the
updated instructions). Unit-test with a fake clock; no hardware.
