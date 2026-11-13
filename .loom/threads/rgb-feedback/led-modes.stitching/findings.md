# led-modes findings (Bob's K16_N3, fw 103)

Script: `probe.py` beside this file (led-probe's, plus `light <11-byte hex>`),
baseline `../led-probe.tied/baseline.json`.

## `06 16` defaults, modes 0–11 (2026-11-13, read only)

Mode 0: `0100000000000000000000`. Modes 1–11 all `01 00 <mode> 04 03 03 00 08 ff ff ff`
(the same block as mode 12). (observed)

## Vendor layout file for `36ae:2475` (desk, 2026-11-13)

From the configurator chunk for `./36ae_2475.json` on `www.sdcx-tech.com`
(the bare domain's TLS certificate didn't match on 2026-11-13). Nothing of it
saved here. (documented)

- `lightingConfig`: `brightnessLevel` 5, `speedLevel` 3. `matrix` 4 rows × 7 cols.
  **`mcu_type` "9520"**; the bundle's update code distinguishes `M9520`, `M951`,
  `M9800` and `AT405` (Artery) and reads `user_size` / `boot_size` /
  `boot_startaddr` per MCU type (for `firmware-feasibility`).
- Per-mode flags (`direction` is false for every mode):

| value | vendor name | brightness | speed | color | palette |
|---|---|---|---|---|---|
| 0 | Off | – | – | – | – |
| 1 | Steady | ✓ | – | ✓ | ✓ |
| 2 | Breathing | ✓ | ✓ | ✓ | ✓ |
| 3 | Spectrum | ✓ | ✓ | – | ✓ |
| 4 | Left-right flow | ✓ | ✓ | ✓ | ✓ |
| 5 | Up-down flow | ✓ | ✓ | ✓ | ✓ |
| 6 | Raindrop | ✓ | ✓ | ✓ | ✓ |
| 7 | Meteor | ✓ | ✓ | ✓ | ✓ |
| 8 | Starry sky | ✓ | ✓ | – | ✓ |
| 9 | Ripple (stays lit) | ✓ | ✓ | – | ✓ |
| 10 | Ripple (fades) | ✓ | ✓ | – | ✓ |
| 11 | Lit on press | ✓ | ✓ | ✓ | ✓ |
| 12 | Custom | ✓ | – | – | ✓ |

## LEDs off for Bob's board photos (2026-11-13, Bob asked)

- Sent `06 0b 0b 00 00 01 00 00 00 00 00 00 00 00 00 00` (glra-studio's tested
  Off; equals the `06 16` mode-0 block). Ack 14.76 ms (slower than earlier
  `06 0b` acks of 1.6–2.6 ms). `06 0a` = `0100000000000000000000`; colour
  table and keymap mirror unchanged. Persists, presumably. (observed)

## How the configurator builds the 11 bytes (desk, 2026-11-13, documented)

`setLightConfig` sends `[type, 0, mode, brightness, speed, direction, color, 0, h, s, v]`
with `06 0b 0b 00 00` in front; for mode 0 it forces `color` to 0.
- brightness: UI slider 0–4. speed: UI slider 0–4 (though `speedLevel` says 3).
- `color`: 1 when the "single colour" checkbox is ticked, else 0 (multicolour).
- byte 7: read back as `singleColorIndex`, always written as 0 by the UI.
  Bob's stock state has 8 there, as does every `06 16` default.
- h/s/v: the UI's 0–360 / 0–100 / 0–100 scaled to 0–255.
- direction is never exposed in the UI (no mode flags it).
- The colour picker panel is hidden when a mode supports `color` but the
  checkbox is off, or the mode has no `palette`.
