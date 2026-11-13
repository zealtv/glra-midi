# orientation — the pad held any of four ways

Suggested model: Sonnet. Build to `docs/config-app.md`.

Bob, 2026-11-13: "and have an orientation selector." Earlier that day, after
seeing the firmware's left-right flow (mode 4) in `led-probe`, Bob read the
vendor's intended frame as **dials on the right**; as of 2026-11-12
`glra_osc/device/layout.json` numbers keys for the way Bob holds it: dials along
the top edge, key 1 top-left, row-major, dials 1–3 left to right
(`glean:k16n3-hid-interfaces`).

- `glra_osc/orientation.py`, pure: the four rotations (`dials-top`,
  `dials-right`, `dials-bottom`, `dials-left`; formulas and dial order in
  `docs/config-app.md` §6.2); for each, physical control → displayed number,
  grid position (row, column) and dial order, and back. Physical ids are today's `layout.json`
  names; the profile stores assignments by physical id, so changing orientation
  remaps nothing.
- Dials-top must reproduce today's numbering exactly.
- cw/ccw stay physical (a clockwise turn is clockwise however the pad lies).
- The profile's `[pad] orientation` (added by `profile-model`); `monitor`
  labels events with the displayed numbers when a profile is in use, physical
  id in brackets (`KEY 01 [key.13] DOWN`).
- A note in the design or README that firmware animations run in the vendor's
  frame whatever the chosen orientation.

Tests: each rotation is a bijection; four quarter-turns return to the start;
dials-top equals `layout.json`; the worked 4×4 table for dials-right from §6.2 in
the test file so a reader can check it by eye. Bob confirms the directions at the pad on
the tour.
