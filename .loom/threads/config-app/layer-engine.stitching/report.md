# layer-engine: report

Claude (Sonnet worker), 2026-11-13, branch `layer-engine`. Pure code and tests;
no device I/O. `./test.sh` passed (268 tests) before the commit and again after
merging `main` (the merge brought only loom renames).

## What I built

`glra_osc/engine.py`, built to `docs/config-app.md` §3 (minus glides).
`Engine(profile, layer=1, on_layer=None)`; still pure, no clock.

- **Resolution** (§3.1): layer key, else the global event, else the active
  layer's event, else nothing. No fall-through, no override.
- **Layers** (§3.2): `layer-set n`, `layer-inc`, `layer-dec` (wrapping) act on
  press, send nothing, and work from every layer. `on_layer(old, new)` fires
  only when the layer changes; `Engine.layer` reads it. A `layer-set` past the
  count is ignored. `layer=` on the constructor lets `runner-profile` keep the
  active layer across a reload (falls back to 1 if it no longer exists).
- **Releases** (§3.3): each held control remembers the event its press
  resolved to, so a layer change in between can't strand a note.
  Repeated `down` and stray `up` are ignored for every kind.
- **State** (§3.4): latch per (control, layer) for per-layer controls, one per
  global control; one CC value per (channel, cc), seeded from absolute dials'
  `initial`, shared by `cc-set`, `cc-step`, `cc-momentary` and `cc-absolute`;
  `Engine.cc_value(channel, cc)` exposes it for tests.
- **Kinds** (§3.5, jump only): `note` (momentary, latch), `cc-momentary`
  (momentary, latch), `cc-set` (always sends), `cc-step` (sends only on
  change, clamped), `cc-absolute`, `cc-relative`. Per-event `channel`.
- **`release_all()`** (§3.7 minus glides): Note Off for held and latched notes
  (latches reset), held `cc-momentary` back to `low`; latched CCs and the
  value table stay.
- **Control names.** `profile.py` names a turn `enc.N.turn`, `events.py` emits
  `enc.N` for turns; `handle` maps one to the other. Presses (`key.N`,
  `enc.N.push`) match as they are.
- `runner.py`: one line so `run` keeps working: `Engine(profile_from_mapping(mapping))`.
  `runner-profile` replaces it with real profile loading.
- `tests/test_engine.py`: the old tests ported to the legacy adapter (none
  deleted), plus new ones: every kind global and per-layer, no-event layers,
  layer keys, wrap, layer change while held, latch per layer, no fall-through,
  shared CC value across set/step/momentary/dial, `release_all`.

## What I didn't build

- Glides, `tick`, `next_due` (`cc-easing`). `ease-ms` and `curve` are read
  but ignored; every CC change jumps. I kept `_send_cc` and `_undo` as the
  single places a CC goes out, where `cc-easing` can hook in.
- No runner wiring for layer-change printing (`runner-profile`).
- Orientation labels on events (`orientation`/later stitches).

## Choices worth a look

- A latched `cc-momentary` toggles its own latch flag, not the CC value; if
  another control changes that CC, the next press still toggles from the flag.
  Matches the design's "latched CC keeps its value".
- `cc-momentary` press and release always send (as before); `cc-step` and
  absolute turns send only on a change.
- Controls with an unnumbered or unknown name still produce nothing.

## How I checked

`./test.sh` (ruff + 268 unittest). Fake events only; nothing touched the pad.
Real-pad behaviour (held key across a layer change on the actual hardware)
stays for the tour.

## Open questions

None for Bob; no `questions.md`.
