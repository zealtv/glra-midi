# The K16_N3's SDCX MCU can't practically take our own firmware; own firmware would mean a new controller board

When considering custom firmware, QMK/Vial, flashing, the vendor updater (`55`/`5a`), or the `J1` header on the pad's PCB.

## Triggers
- QMK
- Vial
- custom firmware
- reflash
- flashing
- bootloader
- 5566:0009
- J1
- 55 ff
- 5a a0
- SDC32K
- M9F9520
- M9F951
- Masses Chip
- ZXW
- selection catalogue
- cs@masses-chip.com

## Context
As of the 2026-11-13 desk study (`loom:firmware-feasibility`,
`.loom/dropped/rgb-feedback/firmware-feasibility.tied/feasibility.md`), with
Bob's photos (`lore:2026-11-13-k16n3-board-photos`):
- `U1` is marked `SDCX SDC32K 952CCU6` (read off a photo); vendor
  `mcu_type "9520"`: 32 KB flash, app at `0x0000–0x77FF`, a 2 KB
  **flash-resident** bootloader at `0x7800` that enumerates as `5566:0009`.
  No crystal, no EEPROM: settings live in the MCU's own flash.
- Leading but **unconfirmed** chip candidate (2026-11-13, an outside agent's
  report, `lore:2026-11-13-mcu-chip-lead-m9f9520`): ZXW / Masses Chip `M9F9520`
  (32K, full-speed USB, WS2812, 48-pin). ZXW's catalogue lists it, together with
  an `M9F951`, which matches the updater's `951` / `9520` names. If a datasheet
  and a read-capable programmer turn up, the "no backup" point below may change.
  Tracked in `loom:firmware-approaches` (under `custom-firmware`, parked by Bob on 2026-11-13).
- A second search by the same outside agent (2026-11-13,
  `lore:2026-11-13-further-chip-findings-m9f9520`, not reproduced by us) reports
  a Masses Chip "FLASH MCU Selection Catalogue (2025)" PDF listing `M9F9520`
  (and `M9F951`, `M9F9800`): 32 KB flash, 2 KB RAM nominal (ZXW's page says
  2216 bytes), 44 I/O, 15-level hardware stack, three 16-bit timers, eight 8-bit
  PWM outputs, USB 2.0, 2.2–5.5 V, 48 pins. The same search found no `M9F9520`
  datasheet, pinout or programming manual (Masses Chip downloads, ZXW's
  downloads page and the document archive holding the catalogue all lack one),
  and warns that `M9F951` differs in stack depth, I/O and peripherals, so its
  pinout and programming procedure shouldn't stand in for `M9F9520`'s. It
  drafted a Chinese enquiry to `cs@masses-chip.com` (datasheet, pin
  definitions, programming interface, tools, flash readback); as of 2026-11-13
  nobody has sent it, and sending stays Bob's call. Nothing yet confirms that
  `SDC32K 952CCU6` is `M9F9520` silicon: settle that before any programmer
  touches `J1`.
- The vendor images decode as an unidentified 16-bit-word ISA (not 8051, ARM
  or RISC-V; the worker's reading). No datasheet, compiler or open-firmware
  support found.
- The vendor's `update.json` has **no image for `36ae_2475`** (the
  `0816_2475` image is a `951`-class build, so the wrong chip), and the update
  protocol has no read command: stock firmware 103 can't be backed up.
- Update packets start `55` on the wire with **no `06` prefix**
  (`55 ff 00 00` = jump to bootloader; `5a a0` for Artery). Never send them.
- No boot pin; `J1` (`GND SCK SDA VDD`) looks like a proprietary 2-wire
  programming port. Never connect to it.
- Own firmware would mean a replacement controller PCB (RP2040/STM32 + QMK,
  16 WS2812-style LEDs, 3 encoders) in the same case, which leaves the stock
  board intact. That changes the brief ("retaining stock firmware") and needs
  Bob's decision, recorded here.

## Associations
- [[k16n3-lighting]]
- [[sdcx-prior-art]]
- [[brief-is-direction]]
