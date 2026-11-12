# led-research: per-key and live lighting on the K16_N3

Written 2026-11-12 (desk research plus read-only queries on Bob's pad). Every claim carries a label:

- **documented**: the manufacturer's own configurator code says so (read by us on 2026-11-12), or glra-studio's `docs/protocol.md`
- **reported**: another project's author says so (`parsaj-dev/sdcx-keypad`, tested by that author on a *different* model, HCY-K006 `0816:246f`)
- **observed**: seen on Bob's pad on 2026-11-12 (USB `36ae:2475`, firmware **103**) through allowlisted reads only
- **inferred**: our reading of the above; not yet tested

Firmware matters here: glra-studio's notes come from firmware 100; sdcx-keypad names no firmware; the manufacturer bundle names none either; Bob's pad runs 103.

## Bottom line

1. **Per-key colour very likely exists, and is host-writable.** Both the manufacturer's configurator and sdcx-keypad use the same two commands: a bulk write (`06 12`) and a single-key write (`06 14`) into a 3-bytes-per-key RGB table. That table is what `06 13` reads. (documented, reported)
2. **The "432-byte RGB memory" holds only 84 bytes of colour.** Bytes 0–83 look like a 28-entry RGB table; bytes 84–431 repeat the profile-0 assignment table. (observed; see §4). Writes past byte 83 would land in keymap memory. This looks like the main safety hazard for `led-probe`.
3. **Per-key colour shows only in a "custom" lighting mode**, and on the K16_N3's own mode table that mode has value **12**, not 5 (the value sdcx uses for its model). (documented, from the K16_N3 layout JSON the configurator serves for `36ae:2475`)
4. **Flash versus RAM stays unresolved.** The only flash claim in the sources concerns the global-light write (`06 0b`); per-key writes are reported as "live". Neither source tests power-cycle persistence of per-key writes. `led-probe` has to settle this. (§6)
5. **Rate:** one source reports 180 per-key writes/s on another model with no complaints (reported); nothing says whether the K16_N3 accepts more. Round-trip for an allowlisted read on Bob's pad measures about 3 ms (observed). Writes untested.

## 1. Sources and provenance

| Source | How read | Notes |
|---|---|---|
| `parsaj-dev/sdcx-keypad` README | WebFetch, 2026-11-12 | MIT licence. Author owns one device only (HCY-K006). |
| same repo: `docs/PROTOCOL.md`, `docs/DEVICES.md`, `sdcx/protocol.py`, `sdcx/effects.py` | `curl` of the public `raw.githubusercontent.com/.../HEAD/...` URLs, after WebFetch returned 404 on those paths | Saved in the session scratchpad only, not the repo. Read as text, not run. |
| Manufacturer configurator, `sdcx-tech.com` | `curl` of the public page and its JS chunks, 2026-11-12 | **The bundle changed since glra-studio's 2026-09-11 inspection**: the page chunk is now `app/page-3062dc7bcbc3fad3.js`; the old `page-bb948a9e8b9c0440.js` URL returns 404. I could not diff old against new, so "documented" below means "in the 2026-11-12 bundle". Nothing from it lives in this repo. |
| `../glra-studio` (`docs/protocol.md`, `macropad/lighting.py`, local HEAD `33aa281`) | read | Firmware 100. Only global lighting tested. |
| Bob's pad | `glra_osc.device` allowlisted reads: `06 05`, `06 0a` (×2), `06 13` (×2), plus 200× `06 0a` for timing | No writes. Dump: `rgb-memory-dump.json` beside this file. |

I put nothing about Bob or this project into any request; the URLs and paths above are public.

## 2. Commands

Wire format (documented, both sources agree): 64-byte output report, report ID 0, first byte `06` (configuration group), second byte the opcode. In hidapi on macOS add a leading `00`, as the vendored code does. `T(x)` below means little-endian 16-bit.

Opcodes the 2026-11-12 configurator bundle uses with group 6 (complete list I found by pattern search): `05`, `07`, `08`, `09`, `0a`, `0b`, `0c`, `0d`, `0f`, `10`, `12`, `13`, `14`, `16`, `40`, `41`, `fb` (sdcx also names `fc`, auto-sleep); plus group `55` and `5a` (firmware update; see Hazards). **No separate "save", "apply" or "commit" opcode appears for lighting or per-key colour.**

| Opcode | Purpose | Payload after `06 <op>` | Source / label |
|---|---|---|---|
| `0a` | read global light state | none; reply `aa 0a 0b …`, 11 bytes at byte 5 | documented; observed on 103 |
| `0b` | write global light state | `0b 00 00` then 11 bytes: `type, 0, mode, brightness, speed, direction, color, 0, h, s, v` | documented; glra-studio tested modes 0/1/2/4 on fw 100 |
| `16` | read firmware default 11-byte block for a mode | `00 00 00 01 00 <mode>` (reply = `0a`-shaped block). The configurator uses this before every mode switch: read defaults, set the mode byte, write with `0b`. | documented (bundle, sdcx). Not on the allowlist, so not run. |
| `13` | read per-key RGB table | `3a <offLo> <offHi>`; 56 bytes at reply byte 8 | documented; observed on 103 (allowlisted) |
| `14` | **write one key's colour** | `03 <offLo> <offHi> 00 00 00 <r> <g> <b>`, offset = `3 × key_index` | documented; reported working live on HCY-K006 |
| `12` | **write RGB table in bulk** | `3b <offLo> <offHi> 00 00 00 <data…>` up to 56 data bytes per report; a final short chunk sets byte 2 to `(total % 56) + 3` | documented; reported |
| `10` | write one keymap slot | (glra-studio already uses this for assignments) | documented; observed to work on 103 |

Concrete packets, for review (64 bytes, zero padded; hidapi adds a leading `00`):

- **Single key, slot 3 (Bob's key 1) to red:** `06 14 03 09 00 00 00 00 ff 00 00` (offset = 3 × 3 = 9)
- **Mode switch to Custom (value 12), same other settings as Bob's current state:** `06 0b 0b 00 00 01 00 0c 04 03 03 00 08 ff ff ff`. The configurator would send firmware defaults for mode 12 instead (via `06 16`); we do not know those defaults yet.
- **Restore Bob's current global state:** `06 0b 0b 00 00 01 00 04 04 03 03 00 08 ff ff ff` (the `06 0a` read on 2026-11-12 gives `0100040403030008ffffff`, identical to glra-studio's firmware-100 record, so Bob's state looks untouched from stock).

The two sources differ on `06 14`: sdcx's `_send` writes and never reads a reply (reported), while the configurator sends it through its request/response queue, so it waits for *some* reply (documented). What the pad answers on firmware 103 stays unknown (an ack like `aa 14 …`, probably). The probe should record it, and the driver should drain the input queue so unread replies do not pile up.

### Asynchronous notifications (documented, both sources)

Input reports starting `aa fa` arrive unsolicited when lighting changes through an on-device key. A reader waiting for a reply must skip them. The vendored `Reader.query` already ignores frames whose command byte mismatches, so it tolerates them; a streaming driver needs the same tolerance.

## 3. Light modes and key indices on the K16_N3

The configurator serves a layout/capability file per USB ID; for `36ae:2475` it is named `k16n3` (documented, 2026-11-12 bundle; not copied into the repo). My reading of it, translating the Chinese mode names myself:

| value | name (my translation) | value | name |
|---|---|---|---|
| 0 | Off | 7 | Meteor |
| 1 | Steady | 8 | Starry sky |
| 2 | Breathing | 9 | Ripple (stays lit) |
| 3 | Spectrum | 10 | Ripple (fades out) |
| 4 | Left-right flow | 11 | Lit on press |
| 5 | Up-down flow | 12 | **custom** |
| 6 | Raindrop | | |

- glra-studio calls mode 4 "Rainbow wave"; the vendor name reads "left-right flow". Bob's pad **is in mode 4 now** (observed, `06 0a` twice, identical).
- Custom: brightness honoured, speed/colour/HSV not (documented flags). So the brightness byte (level 4 = max; the file lists 5 brightness levels) probably scales per-key colours, and the HSV `v` byte does not. (inferred)
- Key indices run 0–24, with `key_index_max` 28 in the file. 16 entries carry a key background colour in the drawing data: indices 0–3, 7–10, 14–17, 21–24, i.e. glra-studio's four key rows. The nine entries 4–6, 11–13, 18–20 are the three dials (push / two turns) and carry none. (documented for the index list; the "dials have no LED" reading is inferred)

Mapping from `layout.json` numbering to slot index, using `.loom/tied/midi-mvp/unique-assignments.tied/program.py`'s `key_slot` (verified by Bob on 2026-11-12 for assignments; assumed to apply to LEDs):

```
Bob's key:  1  2  3  4 | 5  6  7  8 |  9 10 11 12 | 13 14 15 16
slot index: 3 10 17 24 | 2  9 16 23 |  1  8 15 22 |  0  7 14 21
RGB offset: 9 30 51 72 | 6 27 48 69 |  3 24 45 66 |  0 21 42 63   (3 × slot)
```

## 4. Observed on Bob's pad (2026-11-12, firmware 103)

Dump: `rgb-memory-dump.json` (taken 22:23 AEDT). `06 13` read twice: **432 bytes, identical both times**. `06 0a` twice, identical. `06 05` status before and after identical (firmware 103, internal PID 0x2475, profile 0 of 6, 1 layer).

**Structure of the 432 bytes** (observed, then inferred):

- **Bytes 0–83** (28 triples): zeros except eight `ff 00 00` triples at slot indices 0, 3, 8, 9, 15, 16, 21, 24. In Bob's key numbering those are keys **1, 4, 6, 7, 10, 11, 13, 16**: a red **X** across the 4×4 key grid (corners plus centre). That fits a per-key colour table with 3 bytes per slot index, 16 key entries, none for the dials (slots 4–6, 11–13, 18–20 all zero). (inferred; the pattern is the evidence)
- **Bytes 84–431**: byte-for-byte equal to the first 348 bytes of the profile-0 assignment table. I checked this against glra-studio's backup taken 2026-11-12 06:38Z (before our assignment writes): `rgb[84:] == assignments["0"][:348]`, true. The current bytes differ from that backup in 25 places past byte 83 only, matching Bob's reprogrammed keys (`loom:unique-assignments`). (observed)
- **Bytes 0–83 equal the 06:38Z stock backup** exactly, so the red X survived the day, including at least one replug. That does not tell us whether the X is factory-programmed (probably) or recreated at boot.
- **Inferred reading:** the read at `06 13` walks a flat region whose first 84 bytes are the colour table and whose remainder is the keymap area. Whether the keymap really shares storage with the colour table, or the firmware just reads adjacent memory, the probe cannot tell from reads alone.

**Timing** (observed, read-only): 200 light reads `06 0a`: round trip min 2.84, median 3.00, p95 3.88, max 4.99 ms. This includes the ~1 ms stale-drain poll inside `Reader.query`, so the device-side floor sits lower. `ioreg` reports a 1000 µs `ReportInterval` for the vendor interface (observed), suggesting a ceiling of about 1000 reports/s on the wire (inferred). Write cost remains unmeasured.

## 5. What each source says about live versus persistent

| Claim | Source | Label |
|---|---|---|
| `light off` "writes one report to the device, which stores it in flash" and survives unplugging | sdcx-keypad README and PROTOCOL §4 (HCY-K006) | reported |
| Per-key writes are "live"; outside custom mode the on-device engine overwrites them | sdcx-keypad README, `effects.py` header (HCY-K006) | reported |
| Host effects ran at 20 fps (about 180 writes/s for 9 keys), diffed so unchanged keys are skipped, capped at 60 fps | `effects.py` | reported (code, not a measurement) |
| "Power-cycle persistence remains untested" for global lighting | glra-studio `docs/protocol.md` | documented (fw 100) |
| No save/apply opcode exists for lighting or per-key colour | bundle search, 2026-11-12 | documented |
| Writing the colour table did not change the "RGB memory" in glra-studio's global-lighting tests | glra-studio | documented (global lighting only) |

## 6. Flash versus RAM: the likely story

Three readings fit the evidence; I cannot rank them with confidence.

- **A. Per-key writes are RAM-only.** The configurator's per-key colour clicks look instant and the other project drives them at 20 fps. This favours A, but the author never tested a power cycle, so "live" says only that the LEDs change at once.
- **B. Per-key writes also hit flash every time.** The configurator has no save step, so persistence would have to happen on each write. A table that stays put across replugs (observed) fits B too, and so would a boot-time default.
- **C. Hybrid.** The mode switch (`06 0b`) goes to flash (reported on HCY-K006 for `off`; likely for any `0b`) while `06 14` stays in RAM.

Practical stance for the probe: treat **`06 0b` as flash-backed** (few writes, every one with a restore ready) and **treat `06 14` as flash-backed until a test says otherwise** (a handful of writes, spaced out; no streaming).

A cheap discriminating test, once Bob agrees to the writes: write one colour to one key, read `06 13` back (the table should show it), unplug and replug, read again. If the colour survives, the write persisted (B or C); if the X pattern returns, it did not (A). A second, noisier hint: the time `06 14` takes to acknowledge. Flash page erases usually take tens of milliseconds on small MCUs (general knowledge, not from these sources), so acks arriving at the same 3 ms as a read point to RAM.

## 7. Hazards for the probe

1. **Offsets past byte 83 in the RGB table appear to coincide with keymap bytes** (§4). A `06 14` with `key_index ≥ 28`, or a bulk `06 12` longer than 84 bytes, could rewrite Bob's key assignments. Hard-limit slot index to the sixteen key slots (0–3, 7–10, 14–17, 21–24) and reject everything else in probe code. Do *not* use bulk write for the first probe.
2. **Never send group `55` / `5a`** (firmware update / bootloader) or `0f ff` (restore factory settings, which wipes keymap, macros and colours). Documented in both sources. Keep them out of any allowlist.
3. **Mode 12 untested anywhere we can see.** glra-studio tested modes 0, 1, 2, 4 on fw 100. Mode 12 comes from the vendor layout file for this USB ID, so it should exist on 103, but the first switch is a leap. The restore packet is above.
4. **Mode 5 versus 12:** sdcx's custom mode is 5 (its model). On this pad mode 5 means "up-down flow". Sending sdcx's value unmodified would just change the animation.
5. glra-studio's guard (full backup plus readback around every write) takes seconds per write; use it for flash-backed writes only.
6. The vendored `protocol.py` has no writes. Probe code needs its own packet builder with a hard allowlist (opcodes `0b`, `14`, plus read `16`), still behind Bob's per-command OK.

## 8. Proposed probe plan for `led-probe`

Each new *command* needs Bob's OK with the exact packet shown first. Reads are free.

**Before anything:** capture a fresh backup with glra-studio's `macropad backup --out …` (or `Reader.backup()`). It includes the 432-byte RGB read and the light state; `rgb-memory-dump.json` shows the current values. Note: `restorable` is `false` in that backup format, so "restore" for the colour table means rewriting the same colours with `06 14`, key by key, verified by `06 13`.

0. **Optional: read the mode-12 defaults.** Add `06 16 00 00 00 01 00 0c` as a read in the probe script only (not in the vendored `protocol.py`). It looks like a pure query, but it sits outside the allowlist, so it needs Bob's OK like any new command. If Bob would rather not, skip it and use the hand-built mode-12 packet in §2.
1. **Zero per-key writes: mode switch only.** Send `06 0b` with mode 12 (one packet, Bob approves). Expectation if §4's reading is right: the pad shows the **red X on keys 1, 4, 6, 7, 10, 11, 13, 16**, everything else dark. Bob confirms by eye. This alone answers "per-key LEDs exist?" and "which index is which key?" for those eight keys without touching the table. Read `06 0a` back; read `06 13`; check the table is unchanged.
2. **One per-key write.** Slot 0 (Bob's key 13) from `00 00 00` to a visible colour, e.g. green: `06 14 03 00 00 00 00 00 00 ff 00`. Record the ack bytes and round-trip. Check `06 13` shows the change and bytes ≥ 84 are unchanged. Bob confirms key 13 lit.
3. **Walk all sixteen key slots** once each (sixteen writes, one per slot, in slot order), Bob noting which physical key lights; compare with the §3 mapping. Flag any slot that lights nothing or lights the wrong key.
4. **Persistence test (decides flash vs RAM, and costs a handful of writes).** Leave one distinctive colour in one slot, read back, ask Bob to unplug and replug, read `06 13` again. Record whether it survived and whether the pad came back in mode 12 or mode 4 (that tests the global write's persistence too).
5. **Rate and latency**, only if step 4 says RAM-only: bursts of `06 14` to one slot with alternating colours, increasing from 10 to 100 to 500 per second for a few seconds each, counting acks and watching for drops; Bob reports visible lag. Skip entirely if step 4 says flash.
6. **Input interference:** with `glra-osc monitor` running and Bob pressing keys/turning dials, repeat a burst from step 5 and compare event counts. (Needs step 5 to be allowed.)
7. **Global animation overlap:** in mode 12 the engine should leave the table alone (reported). Also try one write with the pad in a firmware animation (mode 2) and see whether the key colour shows. Needs one more `06 0b` mode write.
8. **Restore:** write the original `06 0b` payload (mode 4, `0100040403030008ffffff`), rewrite any changed table entries (the X pattern: red on slots 0, 3, 8, 9, 15, 16, 21, 24; zero elsewhere in 0–27), and verify with `06 0a` and `06 13`, both twice. Run the restore also on error.

Stop and ask Bob if: an ack looks unfamiliar; `06 13` bytes ≥ 84 change; Bob sees a key assignment misbehave; or the pad stops answering reads.

## 9. Not captured / open

- What the pad answers to `06 14`, `06 12` and `06 16` on firmware 103. (Not run: not on the allowlist.)
- Whether the K16_N3 has more than 16 LEDs (underglow, dial rings). The table's 28 entries and the X pattern say sixteen; the layout file mentions nothing else. Bob's eyes will tell.
- Whether firmware 103 differs from 100 here. Only the global-lighting read could be compared, and it matched.
- The 2026-09-11 bundle that glra-studio inspected, so I cannot say whether `06 12` / `06 14` appeared in it. They appear in the 2026-11-12 bundle.
- Maximum write rate, latency, input interference, and flash behaviour: all `led-probe`'s job.
