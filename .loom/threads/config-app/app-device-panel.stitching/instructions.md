# app-device-panel — RGB mode, orientation and port in the app

Suggested model: Sonnet. Build to `docs/config-app.md`. **No pad writes while
building**: the fake device and a `--demo` flag stand in for the pad.

- **RGB mode**: a selector over `lighting.py`'s factory modes, with brightness,
  speed and (where the mode takes one) a hue, per `docs/config-app.md` §4.10
  and §5; no direction field. With no `[lighting]` in the profile, Apply stays
  disabled. It edits the profile. "Apply to
  pad" does the one guarded write, in a worker thread as glra-studio's
  `worker.py` does, and reports success, "already set" or the readback error.
  State next to it that each Apply is saved in the pad's memory. No write on
  drag, on save or on open.
- Show the pad's current mode when a pad is connected ("Pad: connected /
  not found"), read-only reads only; the app stays fully usable with no pad.
- **Orientation**: a four-way selector; the pad view redraws and renumbers at once.
- **MIDI port name** and default channel.
- If `glra-osc run` holds the pad, reads may still work (non-exclusive opens);
  find out with the fake first and say in the report what needs the real pad.

Tests (offscreen): each control edits the profile; Apply calls the fake exactly
once and not when unchanged; no-pad state. Captures of the panel and of each
orientation.
