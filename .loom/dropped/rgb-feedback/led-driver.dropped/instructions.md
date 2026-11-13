# led-driver — `glra_osc/lighting.py`: talk to the pad's LEDs

Suggested model: Sonnet.

The device layer for the route chosen in `led-route`:
- `set_key(key, rgb)`, `set_keys({key: rgb})` / full 16-key frame, `set_global(mode, …)`
  as the route supports. Key numbering matches `layout.json` (keys 1–16).
- Only send what changed; enforce the write budget / max rate from `led-route`
  (drop or coalesce, never queue unboundedly).
- Open the vendor interface non-exclusively alongside the `watch` readers; survive
  replug (re-open and resend the current frame on `on_pad`).
- On start, save the user's lighting state; on exit (Ctrl-C, SIGTERM, error)
  restore it. A `glra-osc lights --restore` path for after `kill -9`, like `unsilence`.
- Reuse the vendored `glra_osc/device/` transport; no high-rate backup/readback
  (that's for flash writes only, if route B).
Unit-test against a fake device: diffs, rate limit, restore, replug resend.
