# firmware-feasibility: could Bob's K16_N3 run our own firmware?

Desk study by a worker session, 2026-11-13. Nobody touched the pad. Sources: Bob's
board photos (`lore:2026-11-13-k16n3-board-photos`), the vendor configurator at
`https://www.sdcx-tech.com/` (page chunk `app/page-3062dc7bcbc3fad3.js`, `update.json`
and 61 firmware images it lists, all fetched 2026-11-13 into the session scratchpad,
read as data, never run, nothing kept in the repo), web searches, and a lead from
the `led-ram-path` worker relayed by the manager.

Labels: **documented** (the vendor's own code or files say so), **reported** (another
person says so), **observed** (seen by me in a photo or a byte dump, 2026-11-13),
**inferred** (my reading; untested).

## Answer in short

**Not realistically, not on this board.** As of 2026-11-13 the evidence points to an
SDCX-branded 32 KB MCU running an **unidentified, non-8051, non-ARM, non-RISC-V
instruction set**. No public datasheet, compiler or open firmware for it turned up.
Its USB bootloader sits in flash, not ROM. The vendor publishes **no firmware image
for `36ae:2475`**, and the update protocol has no read command we've seen, so Bob's
stock firmware 103 can't be backed up before anything gets overwritten. Flashing
would be a one-way door into a toolchain that doesn't exist.

To get our own firmware, the realistic route is **new hardware, not a reflash**: a
replacement controller board for the same case (RP2040 or similar, which QMK/KMK
support along with WS2812 LEDs and encoders). That sits outside the brief
("retaining stock firmware") and needs Bob's explicit decision. Otherwise, stay on
stock firmware and use the 12 built-in modes or whatever `led-ram-path` finds.

## 1. Which MCU?

- **Marking** (observed, `album-1/source-3.jpg`; read by eye, may be misread):
  `SDCX` logo, `SDC32K` / `952CCU6` / `4GA83 1201`, a 48-lead quad flat package with
  gull-wing leads (LQFP-48, inferred).
- **Board** (observed): only `U1`, sixteen 4-pin addressable LEDs (`G DI DO V`),
  hot-swap sockets, encoders, USB-C and a handful of passives (`C1`–`C10`, `R2`,
  `R4` "4R7", `L6`). **No crystal**, so USB runs off an internal oscillator
  (inferred). No separate EEPROM or LED driver chip: the MCU drives the LED chain
  directly and keeps settings in its own flash (inferred; fits
  `glean:k16n3-lighting`).
- **Vendor MCU class** (documented, page chunk): the layout file for `36ae:2475`
  says `mcu_type "9520"`. The updater's table:

  | type | user_size | boot_size | boot_startaddr |
  |---|---|---|---|
  | `951` | 28 KB | 4 KB | 0 |
  | `9520` | 30 KB | 2 KB | `0x7800` |
  | `9800` | 16 KB | 2 KB | `0x7800` |
  | `AT405` | 232 KB | 24 KB | `0x08000000` (Artery AT32F405, a Cortex-M4) |

  So the `9520` holds **32 KB of flash**, with the application at `0x0000–0x77FF`
  and a 2 KB bootloader at `0x7800–0x7FFF`. "SDC**32K**" fits 32 KB, and "**952**CCU6"
  fits `9520` (inferred).
- **Sibling comparison** (reported: sdcx-keypad issue #1 by `kittyconf`, 2026-08-24,
  relayed by the manager from the `led-ram-path` worker): board `SD014_K007_12Key_RGB_V1.0`
  (2023-10-19), `0816:2473`, fw 106, controller "SDC4BK 231C6T6", layout `mcu_type "951"`.
  Bob's board is `SD014_K009_16Key_ARGB_V2.0` (2026-6-17), `SDC32K 952CCU6`, `9520`. So
  SDCX ships at least two controller classes under its own marking, and the second
  marking line seems to carry the class (`952…` ↔ `9520`) (inferred from two samples).
- **Instruction set** (observed in the vendor images, then inferred). All 61 images
  the updater lists, for `951` and `9520` alike, decode as **16-bit little-endian words
  with the opcode in the high byte**. Each starts with a two-word jump `df LL` + `f0 HH`
  whose target × 2 gives the byte address. Example: the `951` user image at `0x1000`
  opens `5a df 08 f0` → word `0x085a` → byte `0x10b4`, inside its own region. The
  `951` bootloader image forwards an interrupt vector to `0x0804` words = `0x1008`
  bytes, the user image's vector slot. `0xffff` fills unused vector slots. The
  structure resembles PIC18 (two-word instructions whose second word starts with
  `F`), but the opcodes differ. It is **not** 8051 (no `02 hh ll` LJMP at reset), not
  ARM Cortex-M (no stack pointer / vector table) and not RISC-V. I couldn't match it
  to a known core, so it is probably a proprietary or rebadged Chinese 8-bit core. **Not identified.**
- **Building on `re-prior-art`** (`main:.loom/threads/rgb-feedback/re-prior-art.tied/sources.md`
  §3, 2026-11-13). That worker also reports a third marking, `sdc48k`, on a `0816:246E`
  pad (a Reddit snippet only). It found the `0816_2475` image not to be a Cortex-M
  vector table and listed "WCH CH55x/CH32, Sonix SN32F, Nuvoton, HK/CS32 clones" as
  unexcluded candidates. Its suggested next step (b), decoding the image under other
  core assumptions, is the ISA work above. That work excludes the 8051 parts (CH55x,
  Nuvoton N76), the Cortex-M parts (SN32F, CH32F, HK/CS32) and the RISC-V parts
  (CH32V) (inferred from the instruction encoding). It also finds that the
  `0816_2475` image belongs to the `951` class (4 KB boot at 0, user from `0x1000`),
  so it isn't firmware for Bob's `9520`.
- **Web** (2026-11-13): searches for `SDC32K`, `952CCU6`, `SDC4BK` and for the
  bootloader ID `5566:0009` found nothing relevant, in English or in Chinese.
  `re-prior-art` is running the broad sweep; this is not a final negative.

## 2. Open firmware support

- QMK, Vial, ZMK and KMK need a supported core and HAL. QMK covers AVR, ARM
  (ChibiOS: STM32, RP2040, some Chinese Cortex-M clones), and through community
  forks a few 8051/Sonix parts. ZMK needs Zephyr (ARM/RISC-V). KMK needs
  CircuitPython. **None covers an unidentified 16-bit-word core with no public
  compiler** (inferred from the ISA finding above; general knowledge of those projects).
- No vendor SDK, datasheet or toolchain for the SDCX parts turned up.
- No prior open ports for SDCX pads turned up. The one open project,
  `parsaj-dev/sdcx-keypad`, drives the stock firmware over HID and doesn't replace it
  (reported in `led-research`).
- The LED side would be easy on any supported MCU: 16 WS2812-style LEDs in one chain
  (observed). The blocker is the MCU, not the LEDs.

## 3. Recovery: what undoing a flash would take

- **The bootloader lives in flash, not ROM** (documented: `boot_startaddr "0x7800"`
  inside the 32 KB map). Every `9520`-type image the vendor serves carries its own
  2 KB bootloader at `0x7800`. It opens with a jump into itself and holds USB
  descriptors for a vendor-page (`ff00`) HID device, **VID `5566` PID `0009`**
  (observed, e.g. `36ae_2242.bin`). The `951` family's bootloader (at `0x0000`) uses
  the same `5566:0009` (observed, `version_101.bin`). Several bootloader builds exist
  (the hashes differ between images).
- The configurator only writes `user_size` bytes from address 0 (documented:
  `a.splice(0, 30 KB)`), so a normal update leaves the bootloader alone (inferred).
- **Entry is software-only, as far as we can see.** The updater sends a command to
  the running firmware, which jumps to the bootloader (section 4). No boot pin, boot
  button or DFU strap shows on the board (observed: the photographed side holds
  everything, per Bob). The application owns the reset vector at `0x0000`, so if an
  update dies half-way, whether the chip still reaches `0x7800` is **unknown**. It
  might if erased words run as no-ops up to the bootloader, or if the chip has a
  boot-address option; neither is known (inferred).
- **`J1` (`GND SCK SDA VDD`)** connects to nothing else on the board (observed: no
  I2C peripheral exists). It is most likely the MCU's factory 2-wire
  programming/debug port (inferred). It isn't SWD in any useful sense: the core
  isn't ARM, so ST-Link or CMSIS-DAP programmers won't talk to it. It would need the
  chip vendor's own programmer, which we can't identify or buy. **Don't connect
  anything to it.**
- **No backup is possible.** `update.json` (2026-11-13) has **no entry for
  `36ae_2475`** (documented). It has 67 IDs; the nearest, `0816_2475`, maps to
  `16keysd_v105.bin`, a `951`-class image and so the wrong chip. The bootloader
  commands the configurator uses (connect, start-write, check, end) include **no
  read** (documented). So stock firmware 103 can't be saved or restored: the cost
  to undo a bad flash is a dead pad (inferred).
- Side effect for the current design: the configurator's update check would fail
  on Bob's pad, since `u["36ae_2475"]` is undefined. So the vendor UI shouldn't offer
  Bob an update (inferred from code; not run).

## 4. The vendor update path (groups `55` / `5a`), read-only study

From the page chunk (documented). `sendDeviceData(g, [...])` goes through
`webhid_write_command`, which writes `[0, g, ...payload]` padded to 65 bytes: report
ID 0, then the group byte. Group `06` is the normal config channel. So the update
packets start **`55`** on the wire, with **no `06` prefix**. `re-prior-art`'s
`sources.md` §3 writes them as `06 55 FF …`; the 2026-11-13 bundle says otherwise
(documented, checked by me against `webhid_write_command`).

| Step | Packet (after report ID 0) | Meaning |
|---|---|---|
| `startUpdate` | `55 ff 00 00` | running firmware → jump to bootloader (`951`/`9520`/`9800`) |
| `startUpdateForArtery` | `5a a0` | same, for `AT405` |
| reconnect | – | the page re-opens the first matching HID device; the bootloader enumerates as `5566:0009` (observed in the images), which the filter list includes |
| `conenctBootLoader` [sic] | `55 ff 01 00` | handshake with the bootloader |
| `startWriteRom(addr, len)` | `55 ff 02 04 <addrHi> <addrLo> <lenHi> <lenLo>` | addr 0 and len 30 720 for `9520`; addr 4096 and len 28 672 for `951` |
| `updateRom` × n | raw 64-byte image chunks, report ID 0 then all 64 bytes (via `webhid_send_command`) | no header, no per-chunk checksum or address |
| `checkRom` | `55 ff 04 00` | verify (its reply isn't checked by the UI) |
| `endUpdate` | `55 ff 05 01 01` | finish and reboot |

The `AT405` branch exists in the code but does nothing with the file (documented).
The firmware file comes from `./update.json` keyed by `vid_pid`. Nothing here offers
a dump, a signature check or a rollback (documented by absence; an undocumented
bootloader command could exist).

**Every `55` / `5a` packet stays forbidden**, as `led-research` already said:
`55 ff 00 00` alone would drop the pad into a bootloader we can't safely drive.

## 5. What we'd lose by replacing the firmware

- Vendor configurator and glra-studio compatibility: both speak the stock HID
  protocol (`06 …`), and our `glra_osc/device/` code is built on it.
- Bob's stored keymap (the 25 unique codes, `glean:k16n3-hid-interfaces`), the colour
  table and the 12 lighting modes, unless we reimplement them.
- Firmware 103 itself, permanently (section 3).
- On a new-controller-board route the stock board stays intact in a drawer, so
  nothing is lost and the route can be undone. That is its main appeal.

## Recommendation for Bob

1. **Don't reflash this pad.** Unknown core, no toolchain, no backup and a
   flash-resident bootloader with no boot pin add up to a high risk of a brick and
   no payoff. I'd keep `55`/`5a` and `J1` off limits for good.
2. Keep the stock firmware for `rgb-feedback`. Use the built-in modes (e.g. mode 11
   for press feedback), set rarely, and wait for `led-ram-path` on any RAM-only
   per-key path.
3. If live per-key animation matters enough, the "own firmware" route is a
   **replacement controller PCB** for the same case. It would copy the 4×4 hot-swap
   footprint, 16 WS2812-style LEDs and three encoders and use an RP2040 or STM32
   (QMK/Vial support). That's a real hardware project and a change of brief, so it
   needs Bob's decision recorded in glean (`brief-is-direction`).

## Open questions

- What core is the SDCX `9520`? The ISA notes above might let someone match it
  (`re-prior-art` may find a datasheet).
- Is `J1` really the programming port? Bob could check with a multimeter on the
  **unpowered** board, testing continuity from `SCK`/`SDA` to `U1` pins. That needs
  no power or connection, but it's still his call.
- Does any undocumented bootloader command read flash? Unknown, and not worth
  probing: probing means entering the bootloader.
- Would the vendor send Bob the 103 image on request? Possibly worth an email from
  Bob, if he ever wants an undo path.

## Packets for a later probe

**None proposed.** Nothing in this study needs the pad, and every update-path packet
stays forbidden. Non-HID checks Bob might OK: a sharper, angled photo of `U1`'s
marking, and the unpowered continuity check above.

## Proposed glean finding (for the manager; not written by me)

**id:** `k16n3-firmware-replacement`
**title:** The K16_N3's SDCX MCU can't practically take our own firmware; own firmware would mean a new controller board
**when:** When considering custom firmware, QMK/Vial, flashing, the vendor updater (`55`/`5a`), or the `J1` header.

> As of the 2026-11-13 desk study (`loom:firmware-feasibility`): `U1` is marked
> `SDCX SDC32K 952CCU6` (read off Bob's photo), vendor `mcu_type "9520"`: 32 KB flash,
> app at `0x0000–0x77FF`, a 2 KB **flash-resident** bootloader at `0x7800` that
> enumerates as `5566:0009`. The vendor images decode as an unidentified 16-bit-word
> ISA (not 8051/ARM/RISC-V), with no public compiler or open-firmware support found.
> The vendor's `update.json` has **no image for `36ae_2475`**, and the update protocol
> (`55 ff 00..05`) has no read, so stock firmware 103 can't be backed up. No boot
> pin; `J1` (`GND SCK SDA VDD`) looks like a proprietary 2-wire programming port.
> Never send `55`/`5a` and never connect to `J1`. Own firmware would mean a
> replacement controller PCB (RP2040/STM32 + QMK), which is a change of brief and
> needs Bob's decision.
