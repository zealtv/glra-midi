# config-design: report

Claude (Opus worker), 2026-11-13, on branch `config-design`. Docs only; no
code and no device I/O. `./test.sh` passed before each commit and after
merging `main`.

## What it settled (`docs/config-app.md`)

1. **References** (`references.md`): Novation Components, Akai MPK mini Editor,
   Arturia MCC, Intech Grid Editor, Elgato Stream Deck. Taken: the pad drawn in
   the middle, short tile summaries, one inspector, layer tabs above the pad,
   layer keys shown on every layer, device writes only on an explicit button.
2. **Profile**: TOML with `version = 1`, `[midi]`, `[pad]`, `[layers]`,
   optional `[lighting]`, then `[key.N]` / `[enc.N.push]` / `[enc.N.turn]` on
   physical names. A control holds `kind` directly (global), or only
   `layers.<n>` sub-tables (per-layer), or a layer key (`layer-set` /
   `layer-inc` / `layer-dec`, global by construction). Press kinds `note`,
   `cc-momentary`, `cc-set`, `cc-step` (signed step); turns `cc-relative`,
   `cc-absolute`. Full example in §2.5. Files without `version` load through
   `mapping.py` (kept as the legacy reader) as one global layer. A new
   `default_profile.toml`: 4 layers of notes, dial pushes prev / layer 1 / next.
3. **Engine**: resolution layer key → global → active layer → nothing; a
   release goes to the binding its press started; latch per (control, layer);
   one CC value per (channel, cc) seeded from `initial`; `cc-set` always
   sends; glides take the full `ease-ms` per target, retarget from the current
   value, quadratic curves, 100 Hz while gliding; `release_all` leaves nothing
   sounding and every CC on a named value.
4. **App**: module layout under `glra_osc/app/` (with a pure `summary.py`),
   wireframes for the window, each inspector state and the device panel, tile
   states and summary text per kind, the global / per-layer / layer-key
   switching table, layer tabs, files (atomic save, revert, reload on change),
   validation, offscreen tests that skip without PySide6, and
   `tools/app-capture.sh`.
5. **Lighting**: modes 0–12 with per-mode fields; `[lighting] mode, brightness,
   speed, color`; no direction field; Apply is read-modify-write that keeps
   unmodelled bytes, skips when unchanged, and is the only write path.
6. **Orientation**: `dials-top` (default) / `-right` / `-bottom` / `-left`,
   each 90° clockwise from the last; formulas, dial order and a worked
   dials-right table; the file, cw/ccw and the firmware animations don't follow
   the orientation.

## What changed in later stitches

Edited `instructions.md` for `profile-model`, `layer-engine`, `cc-easing`,
`orientation`, `lighting-modes`, `app-shell`, `app-inspector`,
`app-device-panel` and `runner-profile` so they point at the doc's sections and
match it. The decisions that moved:

- `app-inspector`: global → per-layer now **copies the event to every layer**
  (was: shown layer only, the rest emptied). Copy/paste and undo are out this
  round (go on the tour's "later" list).
- `profile-model`: `mapping.py` stays as the legacy reader; add
  `default_profile.toml`; add `tomli-w`; edit helpers follow §4.6 and report
  what they would discard; removing a layer renumbers the ones above it.
- `lighting-modes`: no direction field; Apply keeps the bytes it doesn't model.
- `layer-engine` / `cc-easing`: the send table (§3.5) and `release_all` (§3.7).

`config-app-review` and `config-app-tour` needed no change; the tour already
collects every `questions.md`.

## Open questions

`questions.md` here, Q1–Q9, each with the default taken: latch on CC
momentary, one ease time both ways, the default profile layout, quadratic
curves, global → per-layer copying, lighting mode names and fields, the
profile location, the starting layer, and the profile path across the
glra-midi rename (Q9 added after merging `main`, which brought in
`loom:public-release`).
