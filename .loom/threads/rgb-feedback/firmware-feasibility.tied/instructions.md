# firmware-feasibility — could the pad run our own firmware? (desk + photos)

Suggested model: Opus. **Needs Bob for photos.** No flashing, no bootloader or
update commands. Asked for by Bob, 2026-11-13.

Why: on stock firmware, host-driven per-key animation looks impossible without
flash wear (`glean:k16n3-lighting`), unless `led-ram-path` finds a way. The
brief says "retaining stock firmware" / "No firmware flashing required"
(`lore:2026-11-12-initial-brief`); the brief is direction, so a change needs
Bob's explicit decision, recorded in glean.

Answer, with sources:
1. Which MCU? Bob opens the case and photographs the board and chip markings
   (and any test pads, boot pins, SWD/UART headers).
2. Does open firmware (QMK, Vial, ZMK, KMK, vendor SDK…) support that MCU and
   its LED driver? Prior ports for SDCX / similar pads?
3. Recovery: is the bootloader in ROM (unbrickable) or flash? Is there a boot
   pin / DFU mode, or an SWD route with cheap tools? What it costs to undo.
4. The vendor's update path (groups `55`/`5a`): what it does, read-only study.
5. What we'd lose: vendor configurator, glra-studio compatibility, stored keymaps.
Write `feasibility.md` beside this file with a recommendation for Bob.

## Photos arrived 2026-11-13 (`lore:2026-11-13-k16n3-board-photos`)

From the photos (markings read by eye; may be misread):
- `U1`: SDCX-branded 48-pin chip, marked roughly `SDC32K` / `952CCU6` /
  `4GA83 1201`. Vendor layout file: `mcu_type "9520"`; the configurator's
  updater handles `M9520`, `M951`, `M9800`, `AT405` and reads per-MCU
  `user_size` / `boot_size` / `boot_startaddr` (`led-modes` findings).
  Likely a relabelled part: find what's underneath (package, pinout, `CU6` suffix).
- LEDs: 16 four-pin `G/DI/DO/V` parts in a chain, so addressable (WS2812-style);
  board `SD014_K009_16Key_ARGB_V2.0`, 2026-6-17.
- `J1`: four pads `GND SCK SDA VDD`. Candidate SWD (SWCLK/SWDIO) or I2C; check
  against the MCU's pinout before anything is connected.
- Top side (Bob, 2026-11-13, not photographed): "not much on the other side of
  the board - just the encoders and holes for the leds and keyswitches". So
  every component, `U1` and `J1` included, sits on the photographed side.
