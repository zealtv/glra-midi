# mapping-config — the minimal mapping file

Suggested model: Sonnet. No hardware needed.

A small, human-editable file (TOML or JSON, your call; stdlib `tomllib`
reads TOML) that maps logical controls to MIDI:
- global: port name (default e.g. `GLRA K16`), default channel.
- `key.1`…`key.16` and `enc.N.push`: `note` (number, velocity,
  `momentary`|`toggle`) or `cc` (number, on/off values, momentary|toggle).
- `enc.1`…`enc.3` turn: `relative` (CC number + encoding: `twos-complement`,
  `binary-offset` (64±n), `signed-bit`) or `absolute` (CC number, initial value,
  step; clamps 0–127). Default relative encoding: `twos-complement`. Per the
  2026-11-12 research it has the best evidence for both Ableton Live and Bitwig.
- A shipped default mapping that works out of the box: notes 36–51 on the
  keys, CCs on encoders.

Parse and validate it into plain dataclasses, with clear errors that name the
offending key. Unit tests. Bob may later want MIDI-learn or a GUI; leave room
for that but don't build it.
