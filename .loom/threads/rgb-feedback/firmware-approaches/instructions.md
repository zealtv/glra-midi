# firmware-approaches — what routes to our own LED control exist? (sketch)

Sketch; not queued. Bob, 2026-11-13, after choosing route B: "I'd still like to
see what firmware approaches might be possible". Builds on
`glean:k16n3-firmware-replacement` (don't reflash blind; no backup possible).

Candidate approaches to study, cheapest-risk first:
1. **Identify the chip** (Bob is searching; terms in the 2026-11-13 session):
   if the SDCX `9520` turns out to be a known part with a public IDE,
   compiler and programmer, `J1` might become a real recovery path, and both
   own firmware and patching become thinkable.
2. **Patch the stock firmware** (needs 1): add a RAM-only colour command to the
   vendor image. Still needs a flash with no backup unless a programmer can read.
3. **Tap the LED chain**: the 16 LEDs form one WS2812-style chain driven by
   `U1`. An external MCU (RP2040 class) driving `LED1`'s `DI`, with `U1`'s data
   line cut or lifted, would give live per-key control while stock firmware
   keeps keys and encoders. Needs a second USB link (or an internal hub) and
   board surgery; reversible with care.
4. **Replacement controller PCB** in the same case (RP2040/STM32 + QMK/Vial).
Each: risk, reversibility, cost, effort, what it gives `midi-feedback`/`banks`.

## Chip-identification search terms (manager's list for Bob, 2026-11-13)

Not yet searched as of 2026-11-13, except that `firmware-feasibility` and
`re-prior-art` found nothing for the markings, `SD014_K009`, `K16_N3` and
`5566:0009` in English/Chinese web search (see their `.tied/` files).

**Markings, exactly as printed**
- `SDC32K`, `952CCU6`, `SDC32K 952CCU6` (Bob's `U1`, read off a photo)
- siblings: `SDC4BK`, `231C6T6` (12-key `SD014_K007`, sdcx-keypad issue #1);
  `SDC48K` (a `0816:246E` pad, Reddit snippet only)
- boards: `SD014_K009`, `SD014_K007`, `16Key_ARGB`
- "SDCX MCU", "SDCX 芯片", "SDC32K 芯片"

**Vendor**
- `sdcx-tech`, `SDINNOVATION`, reseller brand `HCY` (`szhcykb`)
- Chinese: "深圳 SDCX 键盘", "宏键盘 主控" (macro-keyboard controller),
  "小键盘 方案" (keypad solution / design house)

**Bootloader USB ID** (in every `9520` vendor image's bootloader; might match
a chip vendor's reference bootloader)
- `VID_5566&PID_0009`, "5566:0009", "USB HID bootloader 5566"

**Candidate families** (cheap Chinese USB MCUs with 16-bit instruction words,
48-pin, 32 KB flash; check each datasheet's instruction-set table)
- Sonix SN8F22xx (e.g. `SN8F2288`), USB keyboard/mouse parts
- Holtek HT68FB / HT66FB USB parts
- Cmsemicon (中微, CMS) 8-bit
- Fremont Micro (FMD)
- Jieli (杰理): common in cheap gadgets, known for its own cores
- BYD, Holychip, Yspring
(8051, ARM Cortex-M and RISC-V parts are excluded by the ISA reading in
`firmware-feasibility.tied/feasibility.md` §1.)

**ISA fingerprint** (the most decisive test)
- Every vendor image starts with a two-word jump `df LL` + `f0 HH`
  (16-bit little-endian words, opcode in the high byte; target × 2 = byte address).
- Close to PIC18's `GOTO` (`EF kk` + `F0 kk`) but for the first byte. Search
  "PIC18 compatible" / "PIC18兼容 单片机" and look for an instruction table
  whose two-word jump starts `DF` with a second word beginning `F`.

**Where else to look**
- Chinese marketplaces (1688, Taobao, LCSC/szlcsc) often list relabelled chips
  under the original part number; search `SDC32K` there.
- LCSC/szlcsc parametric search: "USB 32K 8位 LQFP48 键盘" (USB, 32 KB, 8-bit,
  LQFP48, keyboard).
- A sharper, angled photo of `U1` might show a maker's logo or a misread line.

## Approaches in more detail (manager's notes, 2026-11-13)

1. **Identify the chip.** A known part with a public compiler and programmer
   could make `J1` (`GND SCK SDA VDD`) a real backup and recovery path, which
   opens up 2 and own firmware on this board.
2. **Patch the stock firmware** to add a colour command that doesn't save to
   flash. Needs 1 and a programmer that can read (back up) the current image first.
3. **Tap the LED chain.** Cut or lift `U1`'s data line into `LED1`'s `DI` and
   drive the chain from a small RP2040 board. Stock firmware keeps keys and
   encoders; the host gets live per-key control. Needs a second USB link (or a
   hub inside the case) and careful board surgery, but is reversible. The
   least invasive of the hardware routes.
4. **Replacement controller board** (RP2040 + QMK/Vial). Cleanest result, most work.

Next step when picked up: a worker weighs these (risk, reversibility, cost,
effort, what each gives `midi-feedback` / `banks`), or wait until Bob finds
something about the chip.
