# led-ram-path: looking for a non-persistent way to set per-key colour

Desk research, 2026-11-13. No HID access of any kind. Labels:

- **documented**: in the manufacturer's configurator bundle as fetched from
  `https://www.sdcx-tech.com/` on 2026-11-13 (page chunk `app/page-3062dc7bcbc3fad3.js`,
  the same chunk name `led-research` read on 2026-11-12; K16_N3 layout chunk `5680.1d99d859543f75bb.js`).
  Saved in the session scratchpad only; nothing of it in the repo.
- **reported**: `parsaj-dev/sdcx-keypad` (README, `sdcx/effects.py`, `sdcx/protocol.py`,
  `docs/reference-classS.js`, issues #1–#6 with comments), fetched 2026-11-13 through
  the public GitHub API and `raw.githubusercontent.com`. Last push 2026-10-04.
- **observed**: earlier stitches on Bob's pad (fw 103), cited by file.
- **inferred**: my reading; untested.

## Bottom line

1. **The configurator holds no RAM, preview, streaming or "direct" path.** All 17 group-6
   opcodes it uses map to named methods of one device class. The seven left
   unidentified by `led-research` are keymap, macro, URL and profile commands. None
   touches lighting. (documented)
2. **The configurator never previews per-key colour.** In Custom mode, dragging the
   picker only changes UI state. A single `06 14` goes out when you *click a key*.
   The bulk `06 12` method exists but nothing calls it. (documented)
3. **For the global light, the configurator streams `06 0b` with no debounce.** Each
   `onChange` of the colour wheel, saturation slider or hex box sends one `06 0b`.
   The brightness and speed sliders send only on release. (documented) Since `06 0b`
   persists (observed, `led-probe`), the vendor's own UI writes many
   persisted packets per drag. That hints the firmware might defer or coalesce `06 0b`
   saves, but nothing shows it. (inferred)
4. **sdcx-keypad says nothing about per-key persistence.** No issue, commit or doc
   tests a power cycle after `06 14`. Its effect runner streams `06 14` at up to 60 fps
   and restores only the global light on exit. (reported) So "it streams at 20 fps"
   doesn't count as evidence for RAM.
5. **Bulk `06 12` looks like the same table as `06 14`.** It shares that table's
   layout and offsets, and it pairs with `06 13` exactly as `09`/`10` pair with `08`
   for the persisted keymap. Expect it to persist too. (inferred)
6. **Answer as of 2026-11-13: no RAM-only per-key path found in either source.**
   One untested gap remains worth a probe: whether `06 0b` (and `06 14`) commit at
   once or on a short idle timer (see "Candidate packets").

## 1. The unidentified group-6 opcodes

The configurator's device class (documented; sdcx's `docs/reference-classS.js`, copied
from an earlier bundle, has the same method list and bodies for these, reported):

| Opcode | Vendor method | Payload after `06 <op>` | What it does | Lighting? |
|---|---|---|---|---|
| `07` | `getKeyInfosData` | `38 <offLo> <offHi>`, 576 bytes in 56-byte reads | Read. **No caller in the bundle.** sdcx calls it the *factory key table* and uses it for `keymap reset` (`CMD_GET_KEY_INFOS`), reported. | no |
| `09` | `setKeyInfos` | `3b <offLo> <offHi> 00 <layer> 00 <data…>`, 4 bytes/key, last chunk byte 2 = `(len % 56) + 3` | Bulk keymap write per layer (the `06 12` pattern for the keymap). The UI uses it after drag-and-drop combos. | no |
| `0c` | `getMacroData` | `<len> <offLo> <offHi>`, 4096-byte area | Read macros. | no |
| `0d` | `setMacroData` | `<len> <offLo> <offHi> <data…>`, 59-byte chunks | Write macros. sdcx #5 reports that fw 106 drops chunks sent back to back, and that a 10 ms gap between chunks fixes it. | no |
| `40` | `setURLConfig` | `<len> <offLo> <offHi> <data…>`, 128-byte area | Stores the URL for the "open website" key action (HID usage-coded ASCII, `ff`-terminated). | no |
| `41` | `getURLConfig` | `<len> <offLo> <offHi>` | Reads it back. | no |
| `fb` | `setCurrentProfile` | `<profile>` | Selects one of the 6 profiles. | indirect at most (inferred: a profile may carry its own colour table; untested) |
| `fc` | `setAutoSleepTime` | `02 00 00 <lo> <hi>` | Auto-sleep (named in `led-research` via sdcx). | no |

Also in the class: `0f ff` factory reset, `0f 04` macro reset, groups `55`/`5a`
firmware update: never send (documented).

**Dead stubs:** the class defines `setRGBMode`, `setBrightness`, `setLightSpeed`,
`setSingleColorState` and `setLightColorHSV` with **empty bodies** (documented; the
same in sdcx's older copy, reported). Someone planned finer-grained lighting
commands and never wired them up. They give no opcode numbers. (inferred)

**Input reports:** the only unsolicited frame the class handles is `aa fa`, the
light-state notice (documented). Nothing points to a host-driven frame or stream
mode.

**Transport:** a single queue serialises every command, and each one waits for an
input report before the next goes out (`webhid_write_command`). The fire-and-forget
`sendData` is used only for firmware-update data (documented). So the configurator
can't burst faster than the pad acks.

## 2. How the configurator previews colour

Read from the lighting panel and key components (documented):

- **Custom mode (per-key):** the picker's `onChangeColor` only sets a React state
  colour (default `#336dff`). Clicking a key on the drawing, with the Light tab
  open and the current effect named `custom`, calls `updateKeyInfoColor` →
  `setKeyColorInfo` → **one `06 14`** for that key. No preview while dragging, no
  debounce needed, no batch "apply". `setKeyColorsInfos` (`06 12`) is defined but
  has **no caller**. `onResetColors` is a no-op.
- **Other modes (global colour):** the colour wheel, the saturation slider and the
  hex input call `R(hsva)` on every `onChange`, and `R` calls `setLightConfig`, so
  **one `06 0b` per change event**, with no debounce or throttle (the bundle's only
  `debounce`/`throttle` symbols sit in a library chunk, unused here). Touching the
  wheel also forces brightness to 4. In Custom mode `R` returns early.
- **Brightness and speed sliders** send on `onChangeEnd` only (once per release).
  The brightness handler also scales `v` as `v × brightness / 4`.
- **Mode list:** each click runs `06 16` (read defaults) and then `06 0b`.
- A hidden direction pad (`方向`, `hidden: true`) and a hidden preset menu (rainbow,
  waves …) exist. The direction byte takes 0/1 by arrow, keyed on a mode's
  `direction` flag (1, 2, 3 = which axes). Every K16_N3 mode has `direction: false`.
  (documented)

## 3. sdcx-keypad on persistence

- README and `protocol.py`: `light off` "stores it in flash" and survives unplugging
  (HCY-K006). Nothing about `06 14` persistence. (reported)
- `effects.py`: switches to Custom (mode 5 on that model), diffs frames, sends
  `06 14` only for changed keys, caps at `MAX_FPS = 60`, restores the global light
  with `--restore` but **leaves the per-key table as the last frame**. (reported)
  If `06 14` persists on the K006 as it does on Bob's pad, every effect run leaves
  its last frame in flash. No user has reported that as surprising, perhaps
  because nobody looked. (inferred)
- Issues (all states, with comments; 2026-11-13): #1/#2 SD014-K007 `0816:2473`
  (fw 106; PCB `SD014_K007_12Key_RGB_V1.0`, controller marked `SDC4BK 231C6T6`,
  layout `mcu_type` "951"); #4 **G-LRA k6_n1 `36ae:246f`** (fw 100, same vendor ID as
  Bob's pad); #5 fw-106 macro pacing and phantom-macro bugs on HCY-K006; #6 SD-K4
  `7dfa:dcfd` (fw 101). **None mentions per-key colours surviving or resetting on
  power cycle**, flash wear, or any non-persistent mode. (reported)
- Commits: seven, 2026-08-16 to 2026-10-04: initial driver, effects, docs, report
  tool. None about persistence. (reported)

## 4. Bulk `06 12`

- Same 3-byte-per-key table and offsets as `06 14`; 56 data bytes per report, with
  byte 2 = `0x3b`, or `(len % 56) + 3` on the last chunk (documented). That mirrors
  `09` against `10` for the keymap, and the keymap clearly persists.
- No caller in the configurator, so the vendor UI never exercises it (documented). sdcx
  names it `CMD_SET_KEY_RGB_BULK`; I found no record of a hardware test (reported).
- The 432-byte `06 13` read puts keymap bytes from offset 84 onwards (observed,
  `led-research`). A bulk write past 84 bytes risks the keymap.
- Reading: **`06 12` very likely writes the same persisted table**. Its one
  practical value would be fewer commits per full-pad change (two reports for 84
  bytes, against up to 16 `06 14`), if the firmware commits once per report rather
  than once per key. (inferred)

## 5. What's left: commit timing

`led-probe` showed `06 14` survives an unplug "within about a second" (observed), and
`06 0b` survives a ~5 s unplug (observed; a quick unplug wasn't tried for `06 0b`). Ack
times differ: `06 14` takes ~7–10 ms, `06 0b` ~1.6–2.6 ms in modes 0–8 (observed).

- If `06 0b` saves on an idle timer (a common keyboard-firmware pattern, general
  knowledge, not from these sources), the fast ack and the vendor's undebounced
  wheel streaming would both make sense. A deferred save still writes flash, though,
  once per burst. That would allow live **global** colour or brightness
  modulation at modest flash cost (one save per pause), but no per-key animation.
  (inferred)
- The ~8 ms `06 14` ack fits a synchronous program step. A sub-second deferred save
  can't be ruled out from a human unplug. (inferred)
- From the host there's no way to tell whether the flash has wear levelling.
  `mcu_type` "9520" (observed, `led-modes`) remains the lead for
  `firmware-feasibility` and `re-prior-art`.

## Candidate packets for a later probe (Bob to OK each one)

In priority order. Each has an expected outcome and a restore. None is a RAM path; they
only tighten what we know about commit cost.

1. **`06 0b` quick-unplug.** From stock mode 4, send mode 1:
   `06 0b 0b 00 00 01 00 01 04 03 03 00 08 ff ff ff`. Bob pulls the cable **as soon as
   the keys change** (aim < 0.5 s), replugs, then read `06 0a`. Mode 4 back means
   `06 0b` saves lazily; mode 1 means write-through or a timer shorter than the
   unplug. Restore: `06 0b 0b 00 00 01 00 04 04 03 03 00 08 ff ff ff`. Costs 2 writes.
2. **Scripted `06 14` then a hold-off, to bracket a timer.** One `06 14` to slot 0,
   then the script prints "UNPLUG NOW" and Bob unplugs. That gives a reaction time
   of ~0.2–0.4 s, against "within about a second" last time. Packet
   `06 14 03 00 00 00 00 00 00 ff 00` (key 13 green). Restore
   `06 14 03 00 00 00 00 00 ff 00 00` (red, as in the stock X). Only worth it if (1)
   suggests a lazy save exists.
3. **Read `06 07` (factory key table).** `06 07 38 00 00` … through offset 560. A read the
   UI never sends. It would confirm sdcx's "factory table" reading on fw 103 and
   give a restore source for the keymap. Not lighting-related; low priority.
4. **Not recommended now:** `06 0b` with `type` = 0 (the UI always sends 1; the
   meaning is unknown, persists either way), and bulk `06 12` (hazard past byte 83,
   no RAM evidence). If `led-driver` later wants fewer commits per full-table
   change, a same-data rewrite of bytes 0–55 (`06 12 3b 00 00 00 00 00` + 56 current
   bytes) and 56–83 (`06 12 1f 38 00 00 00 00` + 28 bytes) would test acceptance
   without changing anything visible.

## Outside sources noticed (for the manager to pass to `re-prior-art`)

- sdcx-keypad issue #4: **G-LRA k6_n1, `36ae:246f`, fw 100**: a sibling of Bob's
  `36ae:2475` under the same vendor ID; the reporter offers to share data.
- sdcx-keypad issue #1: the SD014-K007 board's controller marking is `SDC4BK 231C6T6`
  (layout `mcu_type` "951"), a lead for identifying the "9520"-family part.
- sdcx-keypad issue #5: fw 106 needs ~10 ms pacing between chunked writes. That
  matters for any bulk write on Bob's pad.
- sdcx-keypad `docs/reference-layout-0816_246f.js` and the issue #1 attachments: other
  models' layout files for comparison.

## Proposed glean text (for the manager; I didn't edit glean)

Add to `k16n3-lighting`, under Context:

> - **No RAM path found** (desk, `loom:led-ram-path`, 2026-11-13): the vendor
>   configurator's group-6 opcodes `07 09 0c 0d 40 41 fb` cover the factory key table,
>   bulk keymap, macros, URL and profile, none of them lighting; its finer lighting
>   methods are empty stubs. Custom mode sends one `06 14` per key *click*, with no
>   preview; `06 12` has no caller. Non-custom colour drags stream `06 0b` undebounced.
>   sdcx-keypad has no persistence data for `06 14`. Open: whether `06 0b`
>   commits lazily (quick-unplug test proposed).
