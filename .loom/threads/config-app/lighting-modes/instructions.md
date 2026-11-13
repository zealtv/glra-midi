# lighting-modes — choose a factory RGB mode, written to the pad on request only

Suggested model: Sonnet. Build to `docs/config-app.md`. **No pad writes in this
stitch**: fake device only (see "Device safety" in the goal).

Bob: "we also want to select the rgb mode from the factory firmware."

- Vendor `../glra-studio/macropad/lighting.py` into `glra_osc/device/` (update
  `glra_osc/device/README.md` and `THIRD_PARTY_NOTICES.md`; keep its headers).
  It validates modes 0, 1, 2 and 4 only, as tested on firmware 100.
- `glra_osc/lighting.py` on top: the firmware-103 mode table from
  `glean:k16n3-lighting` (0 Off, 1 Steady, 2 Breathing, 3 Spectrum, 4/5 flows,
  6 Raindrop, 7 Meteor, 8 Starry sky, 9/10 Ripples, 11 Lit-on-press, 12
  Custom), with brightness 0–4, speed 0–4, and the fixed-hue flag + HSV where
  that finding says it applies. Build and parse the 11-byte payload. Mark in
  code which fields were verified by eye and which weren't (direction).
- Read the pad's current mode (`06 0a`, an allowlisted read).
- `apply(...)`: one guarded write through the vendored path (backup, write,
  exact readback), skipped when the pad already holds that payload. Never
  `06 14`, never `06 12`, never past the 11 bytes.
- Profile `[lighting]` section per the design; `glra-osc lights` prints the
  pad's mode, and `glra-osc lights --apply` writes the profile's choice after
  showing what will change. Nothing writes lighting implicitly: not `run`,
  not profile load.

Tests with a fake reader: payload build/parse for every mode, the skip when
unchanged, readback mismatch reported, out-of-range values refused. In the
report, list the checks that need Bob at the pad (for the tour).
