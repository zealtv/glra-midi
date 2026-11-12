<!-- auto-generated; run glean.sh index to refresh -->

- [[brief-is-direction]] — The brief points a direction; Bob wants a basic working MIDI tool first — When planning or scoping work here, or when tempted to follow the initial brief to the letter: Bob's stated priorities as of 2026-11-12 override it.
- [[glra-studio-reuse]] — glra-studio is the peer repo for device I/O; reusing it makes this project GPL-3.0 — When touching device detection, assignment reads/writes or lighting, or choosing licence/dependencies: start from `../glra-studio/macropad/` rather than reinventing the protocol.
- [[k16n3-hid-interfaces]] — The K16_N3 shows three HID interfaces, and its stock encoders send duplicate codes — When decoding pad input, picking which interface to open, or reasoning about which control was pressed.
- [[keyboard-seize-needs-root]] — Seizing the pad's keyboard interfaces failed without root, so suppression needs another route or root — When trying to stop the pad typing into apps, or seeing 0xe00002c1 / "open failed" on an exclusive open.
- [[midi-binding-rtmidi2]] — MIDI output uses rtmidi2 (virtual port via open_virtual_port), not python-rtmidi — When writing MIDI output code, or if rtmidi2 fails to install or import: the project depends on `rtmidi2`, and a virtual output port was verified on 2026-11-12.
