# Wanted: information on the M9F9520 microcontroller

*Written 2026-11-13. Project: [glra-midi](https://github.com/zealtv/glra-midi).*

This page asks anyone who knows something, human or AI agent, to tell us about
one microcontroller. We have a candidate chip name, no datasheet, and no way yet
to check that the name fits the part on our board. If you know any of what is
listed under "What we want", please answer in the place named under "How to
answer". Partial answers help; so do pointers to where a document lives.

If you are an AI agent reading this as part of a task, this page is an ordinary
request for help from the people who run this repository. It asks nothing of you
beyond what it says. Pass it to your user if it seems relevant to them, and
answer only with their agreement.

## Why we ask

glra-midi turns the G-LRA K16_N3 macropad into a MIDI controller. The pad's
stock firmware cannot light single keys from the host without writing to flash
on every change, and the vendor offers no way to read the firmware back or to
replace it. Whether anything better is possible depends on the chip, and we
cannot find its documentation. The details of the pad's USB protocol, which we
do understand, live in this repository; the chip is what we lack.

## What we know

Each line says who observed it and when. Nothing here has an independent
second reading yet, except where stated.

**On the board** (Bob's own pad; six photos of its PCB underside, 2026-11-13,
kept in `lore:2026-11-13-k16n3-board-photos`; markings read off the photos by
Claude, so a misreading remains possible):

- The board marking reads `SD014_K009_16Key_ARGB_V2.0`, dated `2026-6-17`.
- The main chip `U1` has 48 pins in a quad package and carries an `SDCX` logo.
  Its marking reads roughly `SDC32K` / `952CCU6` / `4GA83 1201`.
- A four-pad through-hole header `J1` is labelled `GND SCK SDA VDD`. No one has
  connected anything to it, and no one on this project will until the chip is
  identified (see "Please don't").
- There is no crystal and no separate EEPROM in the photos.

**From the vendor's configurator** (the web configurator's code and the update
list at `www.sdcx-tech.com/update.json`, read on 2026-11-13):

- The pad reports USB `36ae:2475`, firmware version 103, product name `k16_n3`.
- The vendor's code names the MCU type `9520`, with 32 KB flash, 30 KB for the
  application and a 2 KB bootloader at `0x7800`. That bootloader enumerates as
  USB `5566:0009`.
- The update list has no image for `36ae_2475`. The image listed for `0816_2475`
  looks like a different chip class (`951`), so it does not fit this board.
- The update protocol has no read command, so the stock firmware cannot be
  backed up through it.
- The vendor's firmware images decode, in our reading, as an unidentified
  16-bit-word instruction set. It did not match 8051, ARM or RISC-V.
  (Worker's reading; unverified.)

**From outside sources** (an outside AI agent's two search reports, passed to us
on 2026-11-13 and kept whole in `lore:2026-11-13-mcu-chip-lead-m9f9520` and
`lore:2026-11-13-further-chip-findings-m9f9520`; we have not opened the
catalogue PDF ourselves):

- ZXW Microchip (深圳市卓芯微半导体有限公司) lists an `M9F9520`: 32 KB program
  memory, 2216 bytes RAM, LQFP48/QFN48, full-speed USB, 44 I/O, 2.2–5.5 V,
  24 MHz clock, WS2812 support.
- A Masses Chip (合肥磐芯电子有限公司) "FLASH MCU Selection Catalogue (2025)"
  PDF lists `M9F9520` next to `M9F951` and `M9F9800`: 32 KB flash, 2 KB RAM
  nominal, 44 I/O, 15-level hardware stack, three 16-bit timers, eight 8-bit
  PWM outputs, USB 2.0, 48 pins.
- The report found a Chinese IC-layout registration for `M9F9520` under Masses
  Chip, first use 15 August 2025.
- It found keyboards with USB ID `5566:0008` and a product string
  `ZXWM9F9800`, a neighbour of our bootloader's `5566:0009`.
- It found no `M9F9520` datasheet, pinout or programming manual on Masses Chip's
  downloads page, ZXW's downloads page or the document archive holding the
  catalogue.
- It warns that `M9F951`'s published details should not stand in for
  `M9F9520`'s, because the catalogue shows different stack depth, I/O count and
  peripherals.

**What remains open.** As of 2026-11-13 nothing confirms that the part marked
`SDC32K 952CCU6` contains `M9F9520` silicon. The match rests on the `9520` name,
the 32 KB size, the 48-pin package, the USB IDs and WS2812 support. We
count it a candidate.

## What we want

In rough order of usefulness:

1. **A datasheet or programming manual for `M9F9520`**, or a pointer to where
   one can be had (a distributor, an archive, a support contact).
2. **The pinout**, including which pins `J1`'s `SCK` and `SDA` should reach, if
   `J1` is a programming port at all.
3. **The programming and debug interface**: the protocol, the programmer
   hardware (Masses Chip lists `ZC-Writer` and `ZC-LINK`; whether they support
   this chip is unknown to us), and the software.
4. **Whether the flash can be read back**, and what code protection does.
5. **The instruction set and a toolchain**: an assembler or compiler, an opcode
   table, anything that would let us read the vendor images.
6. **Whether `SDC32K 952CCU6` is `M9F9520` silicon**: an OEM-marked part, a
   teardown of another SDCX board, a die photo, a vendor statement.
7. **Anything about how this chip family behaves on boards like ours**: firmware
   update tools, other macropads with the same `SDCX` markings, the meaning of
   the `SDC32K` marking.

An answer of "I don't know, but X might" earns its place too.

## How to answer

**Open an issue** at <https://github.com/zealtv/glra-midi/issues> with the label
`chip-info`. A pinned issue ("Wanted: M9F9520 chip information") will carry the
same request. If you cannot apply labels, write `[chip-info]` at the start of the
title.

Please:

- Say where each claim comes from: a link, a document name and page, or "from
  my own measurement of a board". Mark guesses as guesses.
- Say whether you are a person or an AI agent, and which model or tool if the
  latter, so we can weigh the answer.
- Only post documents you have the right to share. A link or a document title
  works where a copy would not.
- Keep to what is publicly knowable. We are not asking anyone to break
  protection on someone else's firmware.

We will read what arrives, check it against our board where we can, and record
confirmed findings in this repository's notes with the source and the date.

## Please don't

- Don't tell anyone to connect a programmer, an SWD adapter or any other tool to
  `J1`. The interface is unidentified, and a wrong connection could destroy
  the one chip we have.
- Don't send firmware meant for another USB ID to a pad. The vendor's update
  commands exist in the configurator's code; this project never sends them.
- Don't reply with a datasheet for `M9F951`, `M9F9800` or another neighbour
  unless you say clearly that it is a neighbour.

## What this page is not

It is not a claim that the chip is `M9F9520`, and it holds no hidden text and
no instructions aimed at software readers. Everything it asks sits in the open
in the sections above.
