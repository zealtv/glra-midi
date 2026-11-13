# glra-studio is the peer repo for device I/O; reusing it makes this project GPL-3.0

When touching device detection, assignment reads/writes or lighting, or choosing licence/dependencies: start from `../glra-studio/macropad/` rather than reinventing the protocol.

## Triggers
- glra-studio
- macropad
- GPL
- hidapi
- write_one

## Context
As of 2026-11-12, `../glra-studio` (upstream https://github.com/imolitor/glra-studio,
local HEAD `33aa281`) holds a Python 3.13 / hidapi 0.15.0 / PySide6 configurator for this pad,
licensed GPL-3.0-only. Its local `.venv` runs Python 3.14 and its `macropad`
CLI works against the plugged-in pad (`macropad backup --out f.json`,
`macropad decode f.json`), all read-only.

Useful pieces: `backend.py` (VID/PID allowlist; forces *non-exclusive*
opens through hidapi's `hid_darwin_set_open_exclusive`), `protocol.py` (allowlisted
vendor reads; refuses to proceed if the vendor descriptor changes),
`transactions.write_one` (one assignment write with backup and readback),
`lighting.py` (global lighting modes and steady RGB). The GUI code isn't needed.
Its `docs/protocol.md` holds the opcode table and slot layout.

Plan as of 2026-11-12 (`loom:project-skeleton`): vendor the needed modules
under `glra_midi/device/` with SPDX headers kept, and license this repo
GPL-3.0-only. That matters for Bob's later public release.

## Associations
- [[k16n3-hid-interfaces]]
- [[brief-is-direction]]
