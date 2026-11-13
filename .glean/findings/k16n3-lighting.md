# The K16_N3 has 16 per-key LEDs, but every colour or mode write persists to flash

When writing lighting code, choosing an LED feedback design, or tempted to stream per-key colours to Bob's pad: as of the 2026-11-13 probe, `06 14` and `06 0b` both survive a power cycle, so live per-key animation would wear the flash.

## Triggers
- 06 14
- 06 0b
- 06 16
- 06 13
- mode 12
- per-key
- rgb memory

## Context
Probed on Bob's pad (36ae:2475, firmware 103) on 2026-11-13 with Bob watching:
`.loom/threads/rgb-feedback/led-probe*/findings.md`, script `probe.py`, baseline `baseline.json`.

- **Per-key colour** `06 14 03 <lo> <hi> 00 00 00 <r> <g> <b>`, offset = 3 × slot,
  ack `aa 14 01 …` in ~7–10 ms. Visible at once, but **only in mode 12 (Custom)**.
- Key slot → LED slot equals the assignment slot (`key_slot` in
  `loom:unique-assignments`); all 16 keys confirmed by eye. Dials have no LEDs (inferred).
- **Mode** `06 0b 0b 00 00` + 11 bytes (`01 00 <mode> 04 03 03 00 08 ff ff ff`
  on this pad); ack `aa 0b 01 …`. Mode 12 = Custom (per-key table); stock = mode 4.
  `06 16 00 00 00 01 00 <mode>` reads a mode's default block (mode 12 = the same 11 bytes).
- **Persistence:** both writes survived replug, even unplugged within ~1 s.
  No save/apply step exists. Treat both as flash write-through; budget writes.
- Firmware animations (e.g. Breathing, mode 2) **replace** per-key colours on all
  keys; switching back to 12 brings the stored table back unchanged.
- The 432-byte `06 13` read: bytes 0–83 = 28 RGB triples (16 used), bytes 84+
  mirror the keymap. **Never write past byte 83** or use bulk `06 12` without a
  fresh look; it could rewrite assignments.
- Not tested: max write rate, input interference, bulk `06 12`, flash endurance.
- Bob's stock table holds a red X (keys 1, 4, 6, 7, 10, 11, 13, 16); restore
  target `0100040403030008ffffff` + that X.

## Associations
- [[k16n3-hid-interfaces]]
- [[glra-studio-reuse]]
