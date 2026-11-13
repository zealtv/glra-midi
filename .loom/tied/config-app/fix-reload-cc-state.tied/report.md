# fix-reload-cc-state: report

Claude (Sonnet 5.5 worker), 2026-11-13.

## Built

- `Engine(..., carry=old_engine)` (`glra_osc/engine.py`): the new engine copies the old one's
  CC value table, then seeds `initial` only for (channel, cc) pairs the old table lacks. It keeps
  each `_latched_ccs` entry whose (control, layer-or-global) still holds an *equal* latched
  `cc-momentary` in the new profile (frozen-dataclass equality, so any changed field drops it;
  moving a control between global and per-layer, or to another layer, also drops it).
- `runner.py` passes `carry=old_engine` on reload. `release_all` runs first as before (3.7), so
  notes, held CCs and glides still release; latched CCs keep their value, as the design says.
- `docs/config-app.md` §3.4: one bullet on reloads.

## Not built

Nothing from the stitch left out. I didn't carry the layer-key state or glides (the stitch asked
for neither; `release_all` has settled glides before the swap).

## Checked

- `./test.sh` after merging main: ruff clean, 399 tests OK, 4 skipped. This venv has no PySide6, so
  the app tests skip; the review's 554 count included them. As of this run I haven't run them.
- New tests: `ReloadCarryTests` in `tests/test_engine.py` (turn, reload, next turn sends value+1;
  `initial` seeds only new pairs; `cc-step` builds on the carried value; the carry is a copy;
  an unchanged latch stays latched; a changed, per-layer or removed control drops it; a per-layer
  latch survives per layer, and drops when the event moves layers), and one runner-level test in
  `tests/test_runner.py` (latched CC, file saved, next press unlatches: `[100, 0]`).
- No device I/O; fakes only.

## Open questions

None. Bob decides nothing here.
