# orientation — handle the pad held in different orientations (sketch, for later)

Sketch only. Split when picked up. Not queued: Bob, 2026-11-13, "a stitch for later".

Bob, 2026-11-13, after seeing the firmware's "left-right flow" animation
(mode 4) in `led-probe`: the vendor seems to intend the pad held with the
**encoders on the right**, labelled top, middle and bottom as the brief first
described them. As of 2026-11-12, `glra_osc/device/layout.json` numbers keys
for the way Bob holds it: dials along the top edge, key 1 top-left, dials 1–3
left to right (`glean:k16n3-hid-interfaces`).

Intention: let the user choose an orientation (at least dials-top and
dials-right; maybe all four), so key numbers, dial names/order, and anything
spatial follows it:
- key and dial numbering in `layout.json` / the mapping config
- per-key LED addressing (`key_slot`, `glean:k16n3-lighting`) and any
  host-side animations' directions
- possibly a note that firmware animations (left-right / up-down flow) run in
  the vendor's frame, whatever the chosen orientation

Open: whether clockwise/counter-clockwise naming should change with
orientation (it shouldn't; physical rotation stays the same), and whether
existing user mappings should be keyed by physical slot so a change of
orientation doesn't silently remap them.
