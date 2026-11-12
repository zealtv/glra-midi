# MIDI output uses rtmidi2 (virtual port via open_virtual_port), not python-rtmidi

When writing MIDI output code, or if rtmidi2 fails to install or import: the project depends on `rtmidi2`, and a virtual output port was verified on 2026-11-12.

## Triggers
- rtmidi2
- python-rtmidi
- open_virtual_port

## Context
As of 2026-11-12, `rtmidi2` 1.5.0 has macOS cp313/cp314 wheels and installed
cleanly into the Python 3.14 venv, while `python-rtmidi` 1.5.8 had wheels only
up to cp312. `MidiOut().open_virtual_port(name)` created a port that a second
`MidiIn` client, and a separate process, could list; a note-on sent through it
arrived. API: `rtmidi2.get_in_ports()`, `MidiOut.send_noteon/send_noteoff/send_cc/send_raw`,
`MidiIn.callback = fn(msg, timestamp)`. Audio MIDI Setup's own window wasn't
looked at. `glra_osc/runner.py` (`MidiPort`) sends with `send_raw(*message)`; a loopback
client received note on / CC / note off byte-exact on 2026-11-12. Details:
`loom:project-skeleton` and `loom:midi-out` notes.

## Associations
- [[glra-studio-reuse]]
