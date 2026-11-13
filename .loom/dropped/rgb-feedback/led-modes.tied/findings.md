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

## Stepping through the modes at defaults (`01 00 <mode> 04 03 03 00 08 ff ff ff`)

Orientation in Bob's descriptions: as he holds it, dials along the top edge.

- **1 Steady** (ack 1.73 ms): top row green, second green/yellow, third
  yellow, bottom red: a static gradient running along Bob's columns (dials → far edge). (observed)
- **2 Breathing** (ack 3.68 ms): all keys together, fade up to a colour and
  back to black; colours cycle red, yellow, yellow-green, green, cyan, blue,
  magenta, white; a little under 1 s per colour at speed 3. (observed)
- **3 Spectrum** (ack 1.71 ms): all keys lit together, hue shifting steadily
  through the colours (Bob's rough sequence: blue, cyan, yellow-green, yellow,
  orange, magenta, cyan, blue, cyan, green, yellow, magenta); no fade to black. (observed)
- **4 Left-right flow** (stock; ack 1.54 ms): a hue wheel travelling from Bob's
  bottom row to his top row (towards the dials); each row lit as one; the same
  colour cycle as Spectrum, with a visible snap at magenta and red
  under-represented. In the vendor's apparent frame (dials on the right, Bob's
  bottom edge on the left) that's left → right, which supports Bob's
  orientation reading (`loom:orientation`). (observed / inferred)
- **5 Up-down flow** (ack 1.65 ms): the same hue wheel, travelling from Bob's
  left column to his right; each column lit as one. In the dials-on-the-right
  frame that's top → bottom, i.e. "up-down". With mode 4 this makes a
  consistent case that the vendor's frame has the dials on the right. (observed / inferred)
- **6 Raindrop** (ack 1.68 ms): random keys light in random colours, one new
  key at a time, each fading out; 3–7 keys lit at once; about 4 new keys per
  second at speed 3. (observed)
- **7 Meteor** (ack 1.59 ms): movement from Bob's left to right, concentrated
  towards the right side; hue cycling as well; each row animated
  independently. In the dials-on-the-right frame: top → bottom streaks per
  vendor column. (observed / inferred)
- **8 Starry sky** (ack 1.68 ms): all keys lit, each fading independently
  between random hues at a fairly steady perceived brightness. (observed)
- **9 Ripple, stays lit** (ack **25.88 ms**, the slowest `06 0b` ack seen):
  pressing a key sends a ripple outward from that key; the last press wins
  (a new press takes over); the hue changes with each press, cycling roughly
  white, red, yellow-green, light cyan, blue-purple, white. Reacts to key
  presses on the pad only; the host can't trigger it. (observed)
  Between presses the pad goes **black** after each sweep (Bob's follow-up).
- **10 Ripple, fades** (ack 23.95 ms): the pad sits lit; a press makes keys
  fade *out* in a ripple from the pressed key, then ripple back in with a hue
  shift to a new colour. Several easing curves at play. (observed)
  So the research's translations look swapped against behaviour: 9 ("涟漪常亮",
  "ripple, stays lit") goes dark between presses, while 10 ("涟漪熄灭",
  "ripple, goes out") is the one that stays lit with a dark ripple. One reading:
  the name says what the *ripple* does (a lit ripple on dark vs a dark ripple on lit). (inferred)
- **11 Lit on press** (ack 24.04 ms): dark at rest; each press makes that key
  fade up quickly to the next hue in a cycle (like the earlier cycles but about
  twice as many steps); holding keeps it lit; release fades out over about
  1 s, an exponential-looking curve, slower than the attack. Keys held
  together each get their own hue. (observed)

Ack times: modes 0–8 acked in 1.5–3.7 ms, modes 9–11 in 24–26 ms (and the Off
write 14.8 ms). Every one persists, so ack time doesn't track flash; it may
track the work of setting up the reactive engine. (observed / inferred)

## Variations (Bob OK'd the list, 2026-11-13)
- **Breathing, single blue** `01 00 02 04 03 03 01 00 aa ff ff` (ack 14.81 ms):
  Bob saw blue-only breathing. Readback `01000204030301ffaaffff`: the firmware
  sets byte 7 (`singleColorIndex`) to `ff` itself. The fixed-colour encoding
  (colour flag 1 + HSV) works. (observed)
- **Left-right flow, speed 0** (ack 1.68 ms): slower than speed 3, still moving. (observed)
- **Left-right flow, speed 4** (ack 1.83 ms): faster than speed 3; a colour
  crosses the pad bottom → top in about 400–600 ms. Speed accepts 0–4 here
  despite `speedLevel` 3 (whether 3 and 4 differ wasn't compared side by side). (observed)
- **Left-right flow, brightness 1** (ack 1.99 ms): dimmer than 4 but still
  very visible in a lit room. (observed)

## Restore

`06 0b … 04 04 03 03 00 08 ff ff ff` (ack 1.66 ms); `06 0a` and `06 13` equal
`../led-probe.tied/baseline.json`, two reads each. Pad left in stock mode 4. (observed)

Writes this stitch: 17 `06 0b` (Off, modes 1–11, four variations, restore) and
12 `06 16` reads. Across led-probe and led-modes the pad has taken 21 `06 0b`
and 17 `06 14` writes. (observed)

## Summary: what the host controls in firmware animations

- **Mode** (0–12): one persisted write each. Firmware animations cover the whole
  pad; reactive ones (9–11) respond only to physical presses.
- **Brightness** 0–4: works (1 is dim but clearly visible in a lit room).
- **Speed** 0–4: works (0 slow, 4 about 0.5 s per crossing).
- **Fixed colour**: colour flag 1 + HSV restricts modes that flag `color`
  (1, 2, 4–7, 11) to one hue; multicolour (flag 0) uses the firmware's own cycle.
- **Direction**: not exposed by the vendor; untested.
- Every change is a flash-persisted `06 0b`, so the host can set animations
  rarely (e.g. on a bank change), not modulate them live.
- Orientation: both flows (4, 5) and Meteor (7) point to a vendor frame with the
  dials on the right; Bob's dials-on-top numbering is a 90° rotation of it.
- For feedback ideas: mode 11 (lit on press, per-key hue, hold, ~1 s release)
  already gives per-key press feedback with no host traffic.
