# profile-model — the profile schema: parse, validate, write, migrate

Suggested model: Sonnet. Build to `docs/config-app.md` (it wins over this file).

`glra_osc/profile.py`, pure (no I/O beyond reading and writing the file):
- Frozen dataclasses for the profile: port, default channel, layers (count,
  names), orientation, lighting, and per control either a **layer action**
  (`set n` | `inc` | `dec`) or **events** keyed by layer (`global` or 1..n).
  Press events: note (momentary | latch; note, velocity), cc momentary (low,
  high, easing), cc set (value), cc step (signed step, easing). Each event has
  a channel (default: the profile's). Encoder turns: today's relative and
  absolute kinds, per layer or global, with a channel.
- A layer action is global by construction: a control holding one can't also
  hold events, and the validator says so, naming the control.
- `parse_profile` / `load_profile` with errors that start with the key path,
  as `mapping.py` does; unknown keys stay errors.
- `dump_profile` writes a file that parses back to an equal profile
  (round-trip test over a profile using every kind).
- Old mapping files load as a one-layer profile with everything global;
  `default_mapping.toml` becomes (or is joined by) a default profile that
  documents the format in comments.
- Edit helpers the app will call (return a new profile): set/clear an event,
  set a layer action (clearing that control's events), add/remove/rename a
  layer (removing one drops its events).
- Decide with the design whether `mapping.py` stays as the legacy reader or is
  replaced; keep `Engine` and `./test.sh` working until `layer-engine` lands
  (an adapter from profile to today's `Mapping` for one-layer profiles is fine).

Tests: every kind parses; each validation error names its path; round trip;
legacy file; edit helpers; layer removal.
