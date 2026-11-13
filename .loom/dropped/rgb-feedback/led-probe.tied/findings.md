# led-probe findings (Bob's K16_N3, `36ae:2475`, firmware 103)

Probe run 2026-11-13 with `probe.py` beside this file. Baseline: `baseline.json`
(full `Reader.backup()` plus light `0100040403030008ffffff` and the 432-byte
`06 13` read). Raw packets and replies: `logs/*.jsonl`.

## Step 0: mode-12 defaults read (`06 16`), Bob OK'd

- Sent `06 16 00 00 00 01 00 0c`. Reply after 1.61 ms:
  `aa 16 0b 00 00 01 00 0c 04 03 03 00 08 ff ff ff`, i.e. the firmware's default
  block for mode 12 is `01000c0403030008ffffff`. That equals the hand-built
  payload (baseline with the mode byte set to 12). (observed)
- Light, colour table and keymap mirror unchanged afterwards (double reads).

## Step 1: switch to Custom (mode 12), no per-key write, Bob OK'd

- Sent `06 0b 0b 00 00 01 00 0c 04 03 03 00 08 ff ff ff`. Ack after 1.70 ms:
  `aa 0b 01 00 00 01 00 0c 04 03 03 00 08 ff ff ff` (same ack shape glra-studio
  checks on fw 100). (observed)
- `06 0a` now reads `01000c0403030008ffffff`. Colour table and bytes 84+ of the
  `06 13` read unchanged (double reads). (observed)
- **Bob saw keys 1, 4, 6, 7, 10, 11, 13, 16 lit red, the rest dark.** That's the
  stored table's red X. So the K16_N3 has per-key LEDs, mode 12 shows the
  stored table, and the slot→key mapping from `loom:unique-assignments`
  (`key_slot`) holds for slots 0, 3, 8, 9, 15, 16, 21, 24. (observed, Bob's eyes)
- Ack time is the same as a read (~1.7 ms), which hints the write isn't
  blocking on a flash erase. It isn't proof: the firmware could defer a save. (inferred)

## Step 2: one per-key write (`06 14`), Bob OK'd

- Slot 0 (Bob's key 13) red → green. Sent `06 14 03 00 00 00 00 00 00 ff 00`.
  Ack after 7.97 ms: `aa 14 01 00 00 00 00 00 00 ff 00` (status `01`, echoes
  offset and colour). (observed)
- Slower than reads and `06 0b` (~1.7 ms): maybe a small flash program step,
  though too quick for a full page erase. Not conclusive. (inferred)
- `06 13` shows only slot 0 changed; bytes 84+ unchanged (double reads). (observed)
- **Bob saw key 13 turn green at once.** `06 14` takes effect live in mode 12. (observed)

## Step 4: persistence across a replug

- Bob unplugged the pad for ~5 s with key 13 green in mode 12, then replugged.
  **Bob saw the red X with key 13 still green**, still Custom mode. (observed, Bob's eyes)
- Reads after replug: `06 0a` = `01000c0403030008ffffff` (mode 12 kept);
  `06 13` slot 0 = `00ff00`, every other slot and bytes 84+ as the baseline. (observed)
- So **both `06 0b` and `06 14` persist across a power cycle**: they land in
  non-volatile storage, very likely flash, with no separate save step. (observed;
  "flash" inferred)
- Not yet known: whether each `06 14` programs flash at once (the 8 ms ack hints
  so) or the firmware saves later. Either way, streaming `06 14` for live
  feedback would wear the flash. The rate test (step 5) is skipped, per the
  stitch's rule.

## Step 4b: quick unplug after a write

- 11:24:31: slot 0 (key 13) green → blue, `06 14 03 00 00 00 00 00 00 00 ff`;
  ack 7.67 ms, `aa 14 01 …`. Bob unplugged as soon as he saw the key turn blue
  (within about a second), then replugged. **Key 13 came back blue**; `06 13`
  reads `0000ff` at slot 0. (observed)
- So the firmware commits each `06 14` to non-volatile storage within ~1 s, very
  likely during the ~8 ms ack (write-through), not on a lazy timer. The 10 s
  variant was dropped as redundant: a later unplug can only keep it too.
  (inferred)

## Step 3: walk the eight dark keys (16 `06 14` writes), Bob OK'd

- Batch A: slots 10, 17, 2, 23 → green, yellow, cyan, white. Bob (not told the
  expected keys) saw key 2 green, 3 yellow, 5 cyan, 8 white. (observed)
- Then batch A back to `000000`, and batch B: slots 1, 22, 7, 14 → white, cyan,
  yellow, green. Bob saw keys 2, 3, 5, 8 dark again and key 9 white, 12 cyan,
  14 yellow, 15 green. (observed)
- With step 1 this confirms **every** key: LED slot = assignment slot, mapped by
  `key_slot` (`loom:unique-assignments`). Dial slots weren't written (the probe
  refuses them); there's no sign of any LED beyond the 16 keys. (observed / inferred)
- All acks `aa 14 01 …`, 6.67–9.66 ms (13 writes in all so far, median ~7.7 ms).
  Bytes 84+ unchanged after every write. (observed)
- Writing `000000` turns a key fully off in mode 12. (observed)

## Step 7: firmware animation versus per-key colour

- With five slots changed (keys 9, 12, 13, 14, 15 plus the red X) the pad went
  to Breathing: `06 0b … 02 …`, ack 2.60 ms. **Bob saw the firmware colour on
  all keys**: the animation replaces the per-key colours; it doesn't overlay or
  mask them. (observed)
- Back to mode 12 (`06 0b … 0c …`, ack 1.64 ms): **Bob saw the per-key colours
  return at once.** The table persists underneath, untouched by the mode
  switch (`06 13` unchanged). (observed)

## Step 8: restore

- Six writes: `06 0b` to `0100040403030008ffffff` (ack 2.58 ms), then `06 14`
  slot 0 → `ff0000` and slots 1, 7, 14, 22 → `000000` (acks 7.0–8.7 ms).
- Verified: `06 0a` and the full `06 13` read equal `baseline.json`, two reads
  each. Pad left in mode 4 (left-right flow) as found, at Bob's choice. (observed)

## Not done

- **Step 5 (rate and latency):** skipped. Per-key writes persist, and the stitch
  says to skip it then. Unknown: the max rate the pad accepts.
- **Step 6 (input interference with `glra-osc monitor`):** skipped with Bob's
  agreement, since streaming `06 14` is off the table. Unknown.
- **Bulk write `06 12`:** never sent. Unknown whether it behaves differently.
- The flash part's endurance: not known; no datasheet captured. (not captured)

## Answers to the stitch's questions

| Question | Answer (2026-11-13, Bob's pad, fw 103) |
|---|---|
| Per-key LEDs? Mapping? | Yes, one per key, 16. LED slot = assignment slot via `key_slot`; all 16 confirmed by Bob's eyes. |
| Commands | `06 14` one key (`03 lo hi 00 00 00 r g b`, offset 3 × slot); shows only in mode 12 (Custom), set with `06 0b`. `06 16` reads a mode's default block. |
| Live? | Yes: `06 14` and `06 0b` both visible at once. |
| Flash or RAM? | **Both persist** across a power cycle, even when unplugged within ~1 s of the write. No save/apply step. Treat as flash, write-through. |
| Rate / latency | Ack: `06 14` 6.7–9.7 ms (median ~7.7), `06 0b` 1.6–2.6 ms, reads ~1.7–3 ms. Visible change "at once" to Bob. Max rate not tested. |
| Input interference | Not tested. |
| Animations vs per-key | Firmware animations (Breathing) replace per-key colours; per-key colours show only in mode 12 and come back on return. |

Writes in total: 17 `06 14`, 4 `06 0b`, 1 `06 16` read.

Note on timing: `06 0b` persists too yet acks in ~2 ms, so ack time alone
doesn't tell flash from RAM. The ~8 ms of `06 14` may be the firmware's own
handling, not an erase. (inferred)

For `led-route`: as of this probe only route **B** (per-key via flash, written
rarely) or **C** (global only) is open; nothing found gives route A's RAM path.
