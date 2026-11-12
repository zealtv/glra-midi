# midi-feedback — MIDI input updates pad state (sketch)

Sketch only. Split when picked up, after `midi-mvp`.

Virtual MIDI input port. Incoming CCs update absolute encoder values and
toggle states, so the pad doesn't jump when the DAW changes a parameter. Later
this drives RGB feedback too.

Lighting (2026-11-12): LED feedback for toggles and incoming MIDI goes through
`rgb-feedback` (`led-animator` API). Only that part depends on it.
