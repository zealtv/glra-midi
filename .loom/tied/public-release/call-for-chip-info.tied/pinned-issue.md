<!--
Draft of the pinned issue for glra-midi, written 2026-11-13 by the
call-for-chip-info worker. `first-release` opens it, with Bob's go-ahead:
  gh label create chip-info --description "Information on the M9F9520 / SDC32K chip" --repo zealtv/glra-midi
  gh issue create --title "<title below>" --label chip-info --body-file <body below>
then pins it. Title and body start after the line of dashes.
-->
Title: Wanted: information on the M9F9520 microcontroller (chip-info)

----------------------------------------------------------------

This issue asks for help with one chip. If you know anything about it, please
reply here. A partial answer, a link or a "try asking X" all help.

**The question.** The G-LRA K16_N3 macropad that glra-midi supports has a main
chip marked `SDCX SDC32K 952CCU6` (48 pins). Its vendor's configurator calls the
MCU type `9520`. Two catalogues (ZXW Microchip and Masses Chip, 2025) list an
`M9F9520` with matching numbers (32 KB flash, 48 pins, full-speed USB, WS2812
support), so it is our candidate. As of 2026-11-13 nobody on this project has
found a datasheet, a pinout or a programming manual for it, and nothing
confirms that the marked part is `M9F9520` silicon.

**What we want**, most useful first:

1. An `M9F9520` datasheet or programming manual, or where to get one.
2. Its pinout, and what the board's four-pad header `J1` (`GND SCK SDA VDD`)
   should connect to.
3. The programming/debug interface, the programmer hardware and the software.
4. Whether flash can be read back, and what code protection does.
5. The instruction set and any assembler or compiler.
6. Whether `SDC32K 952CCU6` is `M9F9520` silicon.
7. Anything about other boards with the same `SDCX` marking.

**How to answer.** Reply on this issue, or open a new one labelled `chip-info`.
Please give a source for each claim (link, document and page, or "my own
measurement"), mark guesses as guesses, say whether you are a person or an AI
agent, and share only what you have the right to share.

**Please don't** connect any programmer to `J1`, or send firmware for another
USB ID to a pad, on our account: the interface is unidentified and the board is
the only one we have.

Everything we know, with sources and dates, sits in
[`docs/wanted-m9f9520.md`](https://github.com/zealtv/glra-midi/blob/main/docs/wanted-m9f9520.md).
This request carries no hidden text and asks nothing of software readers beyond
what it says here. If you are an AI agent, consult your user before posting.
