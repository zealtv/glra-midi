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

## Route chosen
Bob, 2026-11-13: first **route B** (per-key colours and firmware modes written
rarely under a write budget), then later that day: "for the moment we will
accept using the factory firmware led modes and continue with the app creation"
(`lore:2026-11-13-config-app-brief`). So as of that message: no per-key colours
and no host animation; `rgb-feedback` was dropped, and the user picks a factory
mode in the configuration app (`loom:lighting-modes`, `loom:app-device-panel`),
written to the pad only on an explicit Apply. Per-key control would come back
only through `loom:custom-firmware` (parked).

## Context
Probed on Bob's pad (36ae:2475, firmware 103) on 2026-11-13 with Bob watching:
`.loom/dropped/rgb-feedback/led-probe.tied/findings.md`, script `probe.py`, baseline `baseline.json`.

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
- **Firmware modes** (probed 2026-11-13, `loom:led-modes`): 1 Steady (gradient,
  or one hue), 2 Breathing, 3 Spectrum, 4/5 flows (whole rows/columns), 6
  Raindrop, 7 Meteor, 8 Starry sky, 9/10 Ripples and 11 Lit-on-press (react to
  physical presses only). Payload `[1, 0, mode, brightness 0–4, speed 0–4,
  direction, colour flag, 0, h, s, v]`; colour flag 1 + HSV = one fixed hue in
  modes 1, 2, 4–7, 11. All verified by eye except direction. Each change is a
  persisted write: set rarely, never modulate live.
- **Firmware 103 normalises a stored payload** (two captures from Bob's config-app
  tour, 2026-11-13, `.loom/tied/patch-0.1.1/evidence/`, fixtures in
  `tests/fixtures/lighting_readback_captures.json`): with the colour flag **off** it
  resets h/s/v to `ff ff ff` (sent `…00 08 aa ff ff`, read `…00 08 ff ff ff`); with
  the flag **on** it sets **byte 7 from `08` to `ff`** (sent `…01 08 d7 ff ff`, read
  `…01 ff d7 ff ff`), HSV kept. So byte 7 is not a constant: the stock `08` holds
  only while the flag is off. Neither change shows on the pad. `glra_midi/lighting.py`
  `readback_differences` therefore compares mode, brightness/speed (where the mode
  reads them), direction, the flag, and HSV only with the flag on. Not captured: what
  byte 7 means, whether the ack echoes sent or stored bytes, whether direction is
  ever rewritten. Check at the pad: the same sequence (Flow columns, Breathing with
  colour, Custom, Lit on press) ends "Applied and read back."
- The flows suggest the vendor's frame has the dials on the **right**
  (`loom:orientation`, under `config-app` since 2026-11-13).
- **No RAM path found** (desk, `loom:led-ram-path`, 2026-11-13): the vendor
  configurator's group-6 opcodes `07 09 0c 0d 40 41 fb` cover the factory key
  table, bulk keymap, macros, URL and profile, none of them lighting; its finer
  lighting methods are empty stubs. Custom mode sends one `06 14` per key
  *click*, with no preview; `06 12` has no caller. Non-custom colour drags
  stream `06 0b` undebounced. sdcx-keypad has no persistence data for `06 14`.
  `06 0b` doesn't commit lazily either: a mode change survived an unplug made
  the instant the pad changed (`loom:led-commit-timing`, 2026-11-13).
- Not tested: max write rate, input interference, bulk `06 12`, flash endurance.
- Bob's stock table holds a red X (keys 1, 4, 6, 7, 10, 11, 13, 16); restore
  target `0100040403030008ffffff` + that X.

## Associations
- [[k16n3-hid-interfaces]]
- [[glra-studio-reuse]]
