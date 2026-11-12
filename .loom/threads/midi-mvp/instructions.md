# midi-mvp — the pad as a silent MIDI controller

**Outcome:** with the G-LRA K16_N3 plugged in, one command starts a headless
process that publishes a virtual CoreMIDI port. Every one of the 25 physical
actions (16 keys; 3 encoders × CW / CCW / push) produces the MIDI a simple
mapping file asks for, and none of the pad's keystrokes reach macOS apps.

The minimum viable product, per Bob on 2026-11-12. Keep it basic. The brief
(`lore:2026-11-12-initial-brief`) points the direction but doesn't specify the
work; see `glean:brief-is-direction`.

## In scope
- Device detection, raw-report decoding into one internal event type.
- A suppression route that keeps the pad silent as a keyboard and fails
  loudly, never silently, when it can't apply.
- Keys: note (momentary or toggle) or CC. Encoders: relative CC or
  absolute CC (0–127 held in software). Encoder push: same options as a key.
- Clean shutdown (no stuck notes), and survive unplug/replug.

## Out of scope for the MVP
MIDI input/feedback, OSC, banks, RGB feedback, GUI, launchd/background
install, release packaging. These are sketched as separate goals and anchored
on this one.

## Order
Children carry `needs/` edges; `.loom/queue` holds the preferred order.
Stitches that need Bob physically at the pad say so at the top.
