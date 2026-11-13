# re-prior-art: other work on the SDCX / G-LRA pad family

Desk research, 2026-11-13. No hardware touched. Labels: **documented** (the source says so in its own docs or
code), **reported** (a third party says they saw it, on the device named), **observed** (I looked at the
artefact myself today), **inferred** (my reading). Downloads (repo docs, vendor JS, `update.json`, one
update `.bin`) sit in the session scratchpad only; nothing copyrighted lives in the repo, and the web requests
carried no information about Bob or this project.

## Bottom line

1. **The family has a small, active circle of reverse-engineering repos (found 2026-11-13, all pushed
   Sep–Nov 2026), and all of them read the same vendor WebHID bundle we already use.** None covers the
   K16_N3 (`36ae:2475`) on hardware; none names the MCU; none has a firmware dump or open firmware.
   So these sources corroborate our protocol notes but add little beyond them for `led-ram-path`.
2. **Independent confirmation of the flash finding.** `dvdarkin/gamekb-k17` states, tested on a different
   model (GAMEKB-K17, `0816:0220`, 2026-10), that colour, lighting and keymap writes "persist in flash
   across unplug and replug" with "no apply or save command" (documented, tested by its author).
   `parsaj-dev/sdcx-keypad` implies the opposite ("a host can repaint individual keys at high rate")
   without testing persistence. Our 2026-11-13 probe sides with the K17 author.
3. **The only fresh lead on a RAM path: keymap type `1F`, "light control" key actions** (firmware
   functions bound to a key: brightness ±, next effect, colour, speed, direction, on/off). They run inside
   the pad, so they don't need host writes, but the K17 author found `1F 01/02` (brightness) did nothing
   in the per-key mode and stored the change in breath mode. Bears on `led-ram-path`: probably not a
   per-key RAM path, but a cheap way to step firmware modes from a physical key. (documented + reported)
4. **MCU:** still unidentified. New hard evidence: the vendor's update tables and the actual update file
   for `0816:2475` say the `9520` part has a **32 KB** flash (30 KB user + 2 KB boot at `0x7800`).
   (observed in the vendor bundle and a HEAD of the `.bin`; see §3.) Bob's board marking
   `SDC32K 952CCU6` fits "32 KB" ("32K") + "952". No datasheet found anywhere.
5. **No open firmware, no firmware dump, no bootloader write-up** exists that I could find. The update path
   (`06 55 FF …`, `06 5A A0`) is documented by three repos, and all three refuse to implement it.

## 1. Sources, one by one

Trust scale: A = tested on hardware by the author and says which; B = read from vendor code, partly tested;
C = derived from vendor code only.

### 1.1 `parsaj-dev/sdcx-keypad` — https://github.com/parsaj-dev/sdcx-keypad
- Python CLI/driver for SDCX/SDINNOVATION pads, `docs/PROTOCOL.md`, `docs/DEVICES.md`. **MIT.** Pushed
  2026-10-04; 3 stars (seen 2026-11-13). Already used by this repo (`led-research.tied`).
- Tested on one device only: HCY-K006 `0816:246f`, MCU type `951` (documented by the author), firmware
  not stated in the README. Trust A for the K006, C for everything else.
- Lists 196 USB IDs across 32 vendor IDs (the same list the configurator accepts), including `36ae:2475`
  (documented, `docs/DEVICES.md`).
- Documents `06 55 FF …` / `06 5A A0` update commands, refuses to implement them, warns of bricking
  with "no recovery path without hardware" (documented).
- **Open issues** (read 2026-11-13): #6 `7dfa:dcfd` SD-K4 (HCY-004, fw 101, bought on Temu, 4 keys; per-key
  colour works for keys 0–3 but `key color all` has no effect, colour readback is empty); #4 `36ae:246f`
  "G-LRA k6_n1" (fw 100, per-key colour works, readback empty); #5 HCY-K006 **firmware 106** drops
  back-to-back macro writes unless a ~10 ms pause separates the 59-byte chunks (reported; reporter fixed
  it locally); #1 `0816:2473`. None names an MCU or K16.
- Bears on: `led-ram-path` (per-key `06 14`, `06 12`), write pacing (10 ms between chunks on fw 106;
  our fw 103 not tested).

### 1.2 `dvdarkin/gamekb-k17` — https://github.com/dvdarkin/gamekb-k17
- Offline config tool and protocol spec for GAMEKB-K17 / HCY-K017 (`0816:0220`, 14 keys, dial, side
  wheel). **MIT.** Pushed 2026-10-15; Windows 11 + hidapi; tests exist; writes are read back.
- `docs/PROTOCOL.md` labels every statement Verified / Observed / "sdcx-keypad" (best epistemics of the
  set; trust A). Key points for us:
  - **Persistence verified:** keymap, colours, lighting persist across unplug/replug; "no apply or save"
    (documented, tested 2026-10).
  - **Effect IDs differ from ours** (K17: 7 = "userlight" = custom; ours: 12). Shows the mode table is
    per-device, as we found.
  - `06 0B` never stores colour bytes [12–15] on the K17 (read back `07 ff ff ff`); our fw 103 stored HSV
    for fixed-colour modes, so models differ (documented/observed contrast).
  - Per-key colours sent right after switching to userlight "can be dropped; wait about 300 ms"
    (reported, K17 only). Our probe saw acks in 7–10 ms; whether colours dropped was not tested.
  - Per-key colours written during an effect are stored and show once userlight is selected (reported,
    matches our observation).
  - Brightness is ignored in userlight (reported).
  - One write round trip about 8 ms; 23 key writes in 0.18 s (reported). Reading config plus 4 KB macro
    area takes about 1.4 s.
  - `1F` function entries (brightness ±, next effect) tested on the K17 side wheel (reported); dial
    entries stored but ignored by the firmware (reported).
  - Profiles: `06 FB` left unresolved; the author never sends it.
- Bears on: flash vs RAM (strong corroboration), `led-ram-path`, write rate, `1F` keymap function keys.

### 1.3 `kabuko/minikbconfig` — https://github.com/kabuko/minikbconfig
- Rust CLI/TUI for SDCX "SIDE-KEYBOARD" pads (`6d7b:dcfa` 3-key, `0816:246f` 6-key). **MIT.** Has a
  48 KB `PROTOCOL.md`. Hardware tests on both models; the TUI is untested (author's words). Trust A/B.
- Reported behaviours (6-key, firmware not named in what I read):
  - Colour **below HSV value 32 doesn't light the pad**; mode 3 (press-lit) then **turns such a colour on
    and never fades it** (the author calls it a firmware bug).
  - The vendor's brightness slider doesn't use the brightness byte; it scales the colour value
    (reported on the 6-key). On our K16_N3, brightness 0–4 did change brightness (observed
    2026-11-13), so the models differ.
  - Per-key colour is raw RGB, visible only in custom mode, and **can't be read back on the 6-key**
    (`key_colors` empty). Our `06 13` read works on fw 103 (observed). A sentence in its docs also says
    command `12` has "no read framing" and a read-back "erased key 1's colour" (documented, line ~571 of
    `PROTOCOL.md`): a hazard note for our "never use bulk `06 12`" rule.
  - Mentions the unrelated CH57x family (`1189:8890`), whose config interface is OUT-only.
- Bears on: `led-driver` clamps (floor of V=32 in HSV modes, perhaps not for per-key RGB), bulk-write
  hazard, `led-modes` brightness findings.

### 1.4 `RiderDeck-8/macropad-movil` — https://github.com/RiderDeck-8/macropad-movil
- Static WebHID configurator plus Android wrapper for SDCX pads; `PROTOCOL.md` (Spanish) and
  `js/protocol.js`, `data/devices.json` (196 IDs), `data/layouts/` (199 layouts). **No licence stated** in
  the page I read, so treat it as all rights reserved. Pushed 2026-09-13. No test suite; manual and demo
  mode only. Trust C.
- Gives the clearest table of key-action **types** (`0x1F` light control with actions 0–25 incl. profile
  change, direction, lock; `0x70` profile wheel; `0x80` open web) and the `06 05` info block layout
  (protocol version, PID, firmware version, profile count, layers, serial at bytes 21–42) (documented).
  Names the update commands as "85 / 90" (decimal for `0x55 / 0x5A`).
- Bears on: the `06 05` field layout (we have it already through glra-studio), `1F` actions.

### 1.5 `djshiye/macropad-fedora` — https://github.com/djshiye/macropad-fedora
- Fedora/GNOME daemon and PySide6 GUI for the 6-key SDINNOVATION pad (`0816:246f`). **MIT.** Pushed
  2026-11-04. Uses an allowlist (reads plus single-key write `16`), refuses `0x55`/`0x5A` and factory reset,
  verifies by read-back; `audit/board_dump.py` dumps stored data read-only. It says firmware isn't
  readable over USB (reported). Doesn't cover lighting. Trust B.
- Bears on: nothing new for lighting. Shows an allowlist + verify design like ours.

### 1.6 `imolitor/glra-studio` — https://github.com/imolitor/glra-studio
- Our peer repo (GPL-3.0). Only repo that names the K16_N3, "G-LRA k16_n3", firmware 100. Pushed
  2026-09-12. Already used; listed for completeness. Found through the repo search with the G-LRA name.

### 1.7 `DarkySoNoSo/MacroPad-k6_n1` — https://github.com/DarkySoNoSo/MacroPad-k6_n1
- "Android USB-HID-Konfigurator für G-LRA k6_n1": a one-line README, no code, no licence (seen
  2026-11-13, pushed 2026-11-12). Worth a re-look later; today it holds nothing.

### 1.8 Vendor sources (documented by the manufacturer's own tooling)
- Configurator: `https://www.sdcx-tech.com/` (bare domain's cert doesn't match). Same page chunk as in
  `led-research` (`app/page-3062dc7bcbc3fad3.js`, still live 2026-11-13). Licence: none granted; read-only
  use as in earlier stitches.
- **`https://www.sdcx-tech.com/update.json`** (observed 2026-11-13, 5.7 KB, 67 entries): maps `VID_PID` to
  `{version, file}`. **`36ae_2475` has no entry**; `0816_2475` does (`16keysd_v105.bin`). Most `36ae_*`
  entries are other (keyboard) products. `0816_246d`–`2479` all have `*keysd_v105.bin` (or `v102` for hub
  variants). So the vendor's updater would not offer firmware for Bob's pad as `36ae:2475`; the same
  hardware seems to ship under `0816:2475` (inferred, from the matching PID and key count).
- `https://www.sdcx-tech.com/16keysd_v105.bin`: HEAD showed 32 768 bytes (Last-Modified 2026-11-11).
  I fetched it to the scratchpad and looked at it read-only (not run): bytes `0x0000–0x0fff` are `FF`,
  data spans `0x1000–0x7eff`, and the first words aren't a Cortex-M vector table (inferred: not plain ARM,
  possibly encoded or an 8051-style / other core). Fw **105**, whereas Bob's pad runs 103. Nothing is
  kept in the repo.

## 2. Other leads that came up and what they are

| Item | What | Verdict |
|---|---|---|
| Reddit r/macro_pads thread (Dec 2024), seen via a mirror in a search snippet | Someone with a VID `0816` PID `246E` pad, chip marked "SDCX sdc48k", asked for software; instructions pointed at sdcx-tech.com which didn't load for them; a commenter mentioned another URL. | Reported; the only hit naming an "sdc48k" marking; I couldn't open the page (mirror host failed to resolve), so claims rest on the search snippet. The marking pattern "SDC<NN>K" suggests the number is flash size in KB (inferred). |
| `kriomant/ch57x-keyboard-tool`, `kamaaina/macropad_tool` | Tools for CH57x pads (VID `1189`) | **Different family**; not applicable, though minikbconfig contrasts the two. |
| `mrminh836/TTCS_T926_K16C2_N3` | Matched "K16_N3" by name | **False positive**: a Vietnamese university project. |
| Hackaday.io 189914 (CH552 macropad custom firmware) | Open firmware for a different cheap pad | Different MCU; only a style model for a port, if we ever reach one. |
| Hackaday "Linux Fu: The Cheap Macropad Conundrum" (2025-07-30) | General cheap-macropad article | Doesn't mention SDCX; no use. |
| DOIO KB16, KiiBOOM Cybrix 16 (QMK/VIA) | 16-key, 3-encoder pads with open firmware | Same look, different hardware; a possible *replacement* path, not prior art. |

Searches that returned nothing relevant (2026-11-13): "SDC32K", "952CCU6", "SD014_K009", "K16_N3" /
"k16n3", `36ae:2475`, "HCY-K006" teardown, AliExpress / Amazon rebrands, firmware dumps, forum posts. The
search tool saw only the Reddit thread and the GitHub repos above. Absence in these results means "not
indexed by this search", not "doesn't exist"; Chinese-language forums (e.g. 21ic, bilibili) and
Taobao/1688 listings weren't reachable, and a Chinese-language query gave nothing.

## 3. The MCU question

- Markings read off Bob's photo: `SDC32K 952CCU6` (from the stitch brief). A Reddit snippet shows
  `sdc48k` on a different PID. Both look like house-branded marks.
- Vendor updater tables (observed in the 2026-11-13 bundle, `eh` object, for `firmware-feasibility`):

  | `mcu_type` | user_size | boot_size | boot start | reading |
  |---|---|---|---|---|
  | `951` | 28 KB | 4 KB | 0 (boot first) | 32 KB flash |
  | `9520` | 30 KB | 2 KB | `0x7800` | 32 KB flash |
  | `9800` | 16 KB | 2 KB | `0x7800` | boot at the same `0x7800` as `9520`, but only 16 KB of user space: flash of at least 32 KB, user area smaller (inferred) |
  | `AT405` | 232 KB | 24 KB | `0x08000000` | Artery AT32F405, 256 KB |

  The `AT405` row is a real Artery part (its family is public); the numeric ones look like the vendor's own
  or relabelled MCUs (inferred). Sizes match "SDC**32K**" for `9520`.
- The update protocol (documented by three repos): `06 55 FF 00 00` start, `01 00` connect bootloader,
  `02 04 …` set address+length, `04 00` check, `05 01 01` end; Artery: `06 5A A0`. The vendor page
  streams the `.bin` after switching the pad into a bootloader mode, i.e. updates come in over the
  same HID interface (documented). Nothing says whether the bootloader can be entered by a hardware
  strap, nor how to recover from a bad write.
- Public candidates I couldn't confirm or exclude: WCH CH55x/CH32, Sonix SN32F, Nuvoton, HK/CS32 clones.
  The 32 KB flash and USB 2.0 full-speed HID with 64-byte reports fit all of them. **No datasheet found.**
- Practical read: no open firmware port or Vial/QMK target is known for this MCU. If `firmware-feasibility`
  wants a real answer, the cheapest next steps are (a) a macro photo of the chip top-marking and a look at
  its pads for SWD/ICSP, (b) the `0816_2475` bin's vector table under other core assumptions, (c) asking in
  `sdcx-keypad`'s issues (a public question, which Bob would need to OK; nothing posted).

## 4. Which open questions the sources bear on

| Open question | Evidence from this stitch | Strength |
|---|---|---|
| Is there a RAM-only colour path? | None found. K17 author tested persistence of per-key writes and found flash (documented, other model). sdcx-keypad's "repaint at high rate" claim is untested. | Negative; consistent with our probe |
| Do `1F` keymap actions give a non-flash route? | Documented action list (movil, K17); tested on the K17 side wheel only. They change firmware state on a key press with no host traffic, but `1F 01/02` stored the new level (flash write per press, reported). | Weak lead |
| Write rate / dropped writes | K17 ~8 ms per write (reported); fw 106 K006 drops back-to-back macro chunks without ~10 ms spacing (reported); wait ~300 ms after entering the custom mode before the first colour (reported, K17). | Use as test list for any burst probe |
| Colour floor / brightness | minikbconfig: V < 32 doesn't light; mode 3 sticks; slider scales V (6-key, reported). Ours differs for brightness (observed). | Check on K16 before the driver clamps |
| Bulk `06 12` hazard | minikbconfig: command `12` "has no read framing", read-back erased key 1's colour (documented). Matches our caution. | Supports "don't use" |
| Which MCU, recovery, open firmware | See §3. | Open |
| Does fw 103 differ from 100/105/106 | 105 ships in the vendor `.bin`; 106 seen in an issue; none of the repos compare versions. | Open |

## 5. Not captured / open

- Whether the pad accepts firmware images meant for `0816:2475` (same hardware?) is unknown; **don't try.**
- A Reddit thread was only seen through a search snippet; its full text and the other URL mentioned by a
  commenter weren't read.
- I didn't read `minikbconfig`'s `DESIGN.md`/changelog, the K17's `DEVICE.md` in detail, nor
  `sdcx-keypad`'s `effects.py`/`protocol.py` (read earlier in `led-research`).
- Not checked: Chinese vendor pages (HCY, szhcykb.com), AliExpress/Amazon listings, Telegram/QQ groups.
- GitHub code search needs a login; unauthenticated repo search hit its rate limit partway, so one batch
  of queries (SDINNOVATION, HCY-K, K16C2, 0816) got no results. WebSearch results stood in for them.

## 6. Packets for a later probe (for Bob to OK; none sent)

None needed from this stitch. If `led-ram-path` wants to test the `1F` idea on the pad, it would be one
keymap write, key slot N = `1F 03 00 00` (next effect), then press that key; that touches the assignment
table (flash), so it needs the usual backup/readback and Bob's explicit OK. I'd rank it below the
`led-ram-path` configurator-opcode work.

## 7. Proposed glean text (not applied; the brief says propose only)

**Finding `sdcx-prior-art`** — *Other repos document the SDCX family but none covers the K16_N3 or names its MCU*

When looking for outside protocol evidence, lighting persistence claims, or firmware/MCU information: as of 2026-11-13, `parsaj-dev/sdcx-keypad` (MIT, K006), `dvdarkin/gamekb-k17` (MIT, K17), `kabuko/minikbconfig` (MIT, 6-key) and `RiderDeck-8/macropad-movil` (no licence) all read the same vendor WebHID bundle. Only the K17 repo tested persistence and found colour/lighting writes persist in flash, which agrees with our probe. No repo names the MCU, holds a firmware dump or implements the update path (`06 55`, `06 5A`). Details: `.loom/threads/rgb-feedback/re-prior-art.stitching/sources.md`.

Triggers: sdcx, gamekb, minikbconfig, prior art, firmware update, 06 55, 9520, SDC32K, update.json

Possible addition to `k16n3-lighting` once confirmed: vendor `update.json` has no `36ae_2475` entry but has `0816_2475` (`16keysd_v105.bin`, 32 KB; observed 2026-11-13); mcu_type `9520` has 30 KB user + 2 KB boot flash.
