# led-demo — `glra-osc lights`: drive the LEDs by hand

Suggested model: Sonnet.

A CLI on top of `led-driver` + `led-animator` so Bob can check it and so
`midi-feedback`/`banks` have a worked example:
- `glra-osc lights set <key> <colour>`, `lights all <colour>`,
  `lights animate <name> [--key K]`, `lights restore`.
- A `--demo` mode cycling: per-key colours, one per-key animation, one whole-pad
  animation, while the pad still plays MIDI under `run` if they can share the
  device (otherwise say so).
README usage. Restores the user's lighting on exit.
