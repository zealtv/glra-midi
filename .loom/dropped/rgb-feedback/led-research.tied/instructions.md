# led-research — find the per-key / live lighting commands (desk only)

Suggested model: Sonnet. No hardware writes; read-only device queries are OK.

Sources, in order:
1. `parsaj-dev/sdcx-keypad` (GitHub): SDCX-family lighting commands, incl.
   per-key host control on another model. Opcodes, payload layouts, and
   whether it says which commands persist to flash vs take effect live.
2. The manufacturer configurator bundle listed in
   `../glra-studio/docs/protocol.md` ("Public manufacturer bundle inspected on
   2026-09-11"): search for the `0x13` RGB read, any matching write, per-key
   colour UIs, "custom"/"user" lighting modes, and any streaming/"direct" mode.
   Save nothing of the bundle in the repo (licence); quote only opcodes and short notes.
3. `../glra-studio` code and docs (`lighting.py`, `protocol.py`'s allowlist).

Also, read-only on Bob's pad (allowlisted reads only, through the vendored
`glra_osc/device/`): dump the 432-byte RGB memory twice and the lighting
state, and look for structure (16 keys × N? 144 × 3?).

Write `research.md` beside this file: candidate commands with payloads, label
each claim documented / reported / inferred, the likely flash-vs-RAM story, and
a short proposed probe plan for `led-probe` (which command first, what to back
up, how to restore). Don't send any write.
