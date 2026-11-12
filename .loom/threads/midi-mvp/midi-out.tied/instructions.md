# midi-out — virtual CoreMIDI port driven by the mapping

Suggested model: Sonnet.

`glra-osc run [--config FILE]`:
- Opens a virtual MIDI output port (through the binding chosen in `project-skeleton`, e.g. rtmidi2 `open_virtual_port`) named
  from config, so DAWs see it as a source.
- A small engine turns `ControlEvent`s into MIDI per the mapping: momentary
  and toggle notes/CCs, relative CC in the configured encoding, absolute CC
  with software state (clamped 0–127).
- Tracks held notes and sends Note Off for everything held on exit,
  disconnect or config reload. No stuck notes.
- Keep the engine pure (events + state in, MIDI bytes out) and unit-test it;
  the rtmidi adapter stays a thin layer around it. This is the seam where OSC
  attaches later as a sibling adapter.
- `--dry-run` prints the MIDI it would send.
