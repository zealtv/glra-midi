# midi-feedback — MIDI input updates pad state (sketch)

Sketch only. Split when picked up. Moved to `backlog` on 2026-11-13 and set to
need `custom-firmware` (Bob, `lore:2026-11-13-config-app-brief`).

Virtual MIDI input port. Incoming CCs update absolute encoder values and
toggle states, so the pad doesn't jump when the DAW changes a parameter. Later
this drives RGB feedback too.

Lighting: `rgb-feedback` and its `led-animator` were dropped on 2026-11-13
(factory LED modes accepted for now). Per-key LED feedback would need
`custom-firmware`. The value-tracking half (incoming CCs update the engine's
CC values and latch states) doesn't need LEDs; `config-app`'s engine keeps a
per-channel CC value table it could write into.
