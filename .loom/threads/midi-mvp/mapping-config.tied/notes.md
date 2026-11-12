# mapping-config notes

Built 2026-11-12. Files: `glra_osc/mapping.py`, `glra_osc/default_mapping.toml`,
`tests/test_mapping.py`, plus a 3-line `[tool.setuptools.package-data]` entry in
`pyproject.toml` so the TOML ships with the package.

## Decisions
- Format: TOML (stdlib `tomllib`; comments let the default file document itself).
- Layout: `[global]` (`port`, `channel` 1–16), `[key.N]`, `[enc.N.push]`, `[enc.N.turn]`.
  A binding holds exactly one of `note` or `cc`; a turn has `type = "relative" | "absolute"`.
- Defaults: velocity 127, cc on/off 127/0, mode `momentary`, relative encoding
  `twos-complement`, absolute initial 64 / step 1. Port `GLRA K16`, channel 1.
- Default file: keys 1–16 → notes 36–51; encoder pushes → notes 52–54; encoder turns →
  relative twos-complement CCs 16–18. (The brief said "CCs on encoders"; the push numbers
  and CC numbers 16–18 are my pick, easy to change.)
- Channel stays 1–16 in the dataclass, as written in the file; `Mapping.midi_channel` gives 0–15.
- Unknown keys are errors (typos shouldn't silently do nothing). Missing controls are allowed
  and mean "unmapped" (partial mappings are valid).
- Errors are `MappingError(ValueError)`, message = `<file>: <key.path>: <problem>`.
- Not built, on purpose: per-binding channel override, MIDI-learn, GUI, writing mappings back,
  and the delta→byte encoding for relative turns (that belongs with `midi-out`, which also owns
  toggle state and the absolute value). Frozen dataclasses keyed by control number keep room for them.
- No CLI flag added (cli.py belongs to event-logger); `midi-out` can call `load_mapping(path)`.

## For Bob's hardware check
- Control numbering follows the 1..16 / 1..3 numbering in the file; which physical key is "7"
  etc. depends on the layout work in event-logger (your pad appears rotated relative to
  glra-studio's diagram, and key 7 produced nothing in the capture passes).
- Confirm in Ableton/Bitwig that twos-complement on CCs 16–18 behaves as the 2026-11-12
  research suggested.
