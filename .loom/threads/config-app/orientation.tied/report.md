# orientation: report

Worker (Sonnet 5.5), 2026-11-13, branch `orientation`. Built to `docs/config-app.md` §6.

## Built

- `glra_osc/orientation.py` (pure): the four rotations as successive clockwise
  quarter turns of the physical grid (`turn_cell`/`unturn_cell`); `key_cell`,
  `key_number`, `physical_key`; `dial_side`, `dial_number`, `physical_dial`
  (dial order per §6.2: dials-bottom and dials-left run enc.3, enc.2, enc.1);
  `display_control` and `label` for physical control names (`key.13`,
  `enc.2.push`, `enc.?`). cw/ccw never enter the module.
- `events.format_event(..., orientation=None)`: with an orientation it prints
  `KEY 01 [key.13] DOWN` and `ENC 3 PUSH [enc.1.push] DOWN`; names that aren't
  controls (`key.unknown:0x65`) keep the plain label. Without one, output is unchanged.
- `monitor --profile FILE`: reads the profile's `[pad] orientation` and labels events with it
  (`monitor.run(profile=...)`, `render(..., orientation=...)`); a bad profile exits 2.
- README note on orientation, including that firmware animations run in the vendor's
  frame whatever orientation is chosen (the design already says so in §6.3).
- `tests/test_orientation.py`: the dials-right worked table from §6.2 (plus the other
  three, derived by hand from the same formulas), bijections, four quarter turns return,
  orientations as successive quarter turns, dials-top equals `layout.json`, dial order checked
  against the same rotation on coordinates, label formats.

## Not built

- `run --dry-run` labels. It reads a mapping, not a profile, until `runner-profile`; that
  stitch should pass `profile.orientation` to `format_event`/`say` where it prints events.
- `monitor` without `--profile` stays unlabelled (physical numbers). Claude's default: explicit
  opt-in, so a broken or absent user profile can't break `monitor`. Bob may prefer it to
  read the user profile automatically; that is a one-line change in `monitor.run`.
- Dial label word: oriented output keeps the log's `ENC` rather than the app's "Dial".

## Checked

`./test.sh` (ruff + 263 unittests) passes, after merging main. No device I/O and no writes
to the pad; the directions have not been checked at the pad (the tour does that, per the stitch).

## Open questions

None needing Bob before the tour. For the tour: do dials-right/-bottom/-left match how he
turns the pad (the formulas come from the design, not from a pad test)?
