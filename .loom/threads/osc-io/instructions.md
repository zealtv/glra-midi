# osc-io — OSC output, then input (sketch)

Sketch only. Split when picked up. Bob wants OSC after MIDI.

OSC output as a sibling adapter on the same event engine as MIDI
(python-osc likely): configurable host, port and paths per control (e.g.
`/key/1 1`, `/encoder/1/delta -1`, `/encoder/1/value 85`). Then OSC input for
parameter updates, bank changes and lighting. The brief's §5 has more ideas;
treat them as options, not requirements.
