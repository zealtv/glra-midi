# profile-model — the profile schema: parse, validate, write, migrate

Suggested model: Sonnet. Build to `docs/config-app.md` (it wins over this file).

`glra_osc/profile.py`, pure (no I/O beyond reading and writing the file):
- Frozen dataclasses for the profile: port, default channel, layers (count,
  names), orientation, lighting, and per control either a **layer action**
  (`set n` | `inc` | `dec`), or one **global** event (the same on all
  layers), or **per-layer** events keyed 1..n. These three exclude each other;
  there is no fall-through from a layer to global (Bob, 2026-11-13).
  Press kinds `note`, `cc-momentary`, `cc-set`, `cc-step`, `layer-set`,
  `layer-inc`, `layer-dec`; turn kinds `cc-relative`, `cc-absolute`; fields,
  defaults and the file shape (a control's table holds `kind` directly for
  global, only `layers.<n>` sub-tables for per-layer) as `docs/config-app.md`
  §2 gives them. Each event has an optional channel (default `[midi] channel`).
  Validate across controls too: `layer-set` above the layer count, and
  conflicting `initial`s for one (channel, cc) (§2.4, §2.9).
- A layer action is global by construction: a control holding one can't also
  hold events, and the validator says so, naming the control.
- `parse_profile` / `load_profile` with errors that start with the key path,
  as `mapping.py` does; unknown keys stay errors.
- `dump_profile` writes a file that parses back to an equal profile
  (round-trip test over a profile using every kind), in the fixed order of
  §2.8, atomically (temp file + rename). Writing uses `tomli-w`, a new pinned
  dependency in `pyproject.toml`. `default_profile_path()` /
  `user_profile_path()` (`~/Library/Application Support/glra-osc/profile.toml`).
- Old mapping files (no `version` key) load through `mapping.py` as a
  one-layer profile with everything global, converted per §2.6.
  `default_mapping.toml` stays; add `glra_osc/default_profile.toml` (§2.7),
  documenting the format in comments, and ship it as package data.
- Edit helpers the app will call (return a new profile), following the
  table in §4.6: set/clear an event; make global (from a given layer);
  make per-layer (copies the global event to every layer); set a layer key
  (clearing that control's events); add/remove/rename a layer (removing one
  drops its events and renumbers the layers above it). Helpers report what a
  change would discard, so the app can ask first.
- `mapping.py` stays as the legacy reader (design §2.6, settled 2026-11-13);
  keep `Engine` and `./test.sh` working until `layer-engine` lands (an adapter
  from profile to today's `Mapping` for one-layer profiles is fine).

Tests: every kind parses; the §2.5 example parses; each validation error
names its path; round trip; legacy file (`default_mapping.toml` and a toggled
CC); the default profile; edit helpers; layer removal and renumbering.
