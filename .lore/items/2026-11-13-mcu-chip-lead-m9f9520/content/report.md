## Chip identification: a strong lead

Likely MCU family found

I searched the markings from your notes—`SDC32K` and `952CCU6`—along with the `9520` firmware identifier and the bootloader USB ID `5566:0009`.

The most promising discovery is ZXW Microchip (深圳市卓芯微半导体有限公司), which lists an MCU called the M9F9520.

Its published specifications are a remarkably close fit:

| Feature        | ZXW M9F9520                   |
| -------------- | ----------------------------- |
| Program memory | 32 KB                         |
| RAM            | 2,216 bytes                   |
| Package        | LQFP48 / QFN48                |
| USB            | Full-speed                    |
| I/O            | 44                            |
| Supply         | 2.2–5.5 V                     |
| Clock          | 24 MHz internal / external    |
| LED support    | 6/8-channel WS2812 capability |

Source: [ZXW Microchip official MCU catalogue](https://zxw-chip.com/article/7?utm_source=chatgpt.com).

This connects several otherwise independent clues: the `9520` firmware identifier, a 32 KB microcontroller, a 48-pin package, and hardware support for addressable RGB LEDs.

I would now put the ZXW M9F9520 at the top of the candidate list. It is not yet a confirmed identification of the `SDC32K`-marked chip; we still need to match its pinout or instruction set. But this is substantially stronger evidence than the earlier generic Holtek/Sonix possibilities.

## Who actually makes it?

The M9F9520 has a second name behind it: Masses Chip (合肥磐芯电子有限公司).

China's National Intellectual Property Administration recorded the M9F9520 IC layout under Masses Chip, with first commercial use listed as 15 August 2025. This independently corroborates that the M9F9520 is a real production chip, not just a reseller's catalogue entry. (cited: cnipa.gov.cn)

Masses Chip also publishes detailed information for the related M9F951, describing it as an 8-bit RISC microcontroller with 32 KB flash, USB 2.0 full-speed operation, programmable code protection, and ISP/IAP firmware programming. (cited: masses-chip.com)

Importantly, Masses Chip maintains a public [software and documentation download centre](https://www.masses-chip.com/c/xzzq?utm_source=chatgpt.com). It lists:

- ZC-LINK — emulator/debugger firmware
- ZC-Writer — programmer firmware
- MCU specifications, examples and development resources

Those tools give us a concrete manufacturer ecosystem to investigate. They do not yet establish that the M9F9520 is supported, or that either tool can read back protected firmware.

## A third clue: the USB bootloader ID

Your notes identify `5566:0009` in the vendor firmware's bootloader.

I found real keyboards using adjacent USB ID `5566:0008`, identifying themselves as ZXWMicroChip. One Linux hardware inventory even reports the USB product string `ZXWM9F9800`—exactly the model of the smaller 16 KB MCU listed alongside the M9F9520 in ZXW's catalogue. (cited: bugs.debian.org +2)

That creates a compelling chain:

Your SDCX firmware — 9520 identifier · embedded USB ID 5566:0009
→ ZXW USB keyboard family — 5566:0008 · ZXWMicroChip / ZXWM9F9800
→ ZXW / Masses Chip M9F9520 — 32 KB flash · USB · WS2812 · 48-pin package

The exact firmware-to-chip relationship is still a hypothesis. But the USB ID, firmware identifier, manufacturer family and hardware specifications now point in the same direction.

## Is the four-pin header a programming interface?

Your `J1` header is labelled `GND`, `SCK`, `SDA`, `VDD`.

A two-signal clock/data programming interface is entirely plausible. Comparable 8-bit microcontrollers use this exact four-wire arrangement, although the signalling protocols differ. (cited: holtek.com.cn)

What I still couldn't establish is the M9F9520-specific programming pinout. Until we have that, I wouldn't connect an ST-Link, generic SWD adapter or other programmer to the header.

The immediate hardware test is unpowered continuity tracing from `J1`'s clock and data pins to the corresponding numbered MCU pins. Those pin numbers can then be compared against an M9F9520 pinout supplied by the manufacturer.

## What's still missing?

| Question                                       | Research result               |
| ---------------------------------------------- | ----------------------------- |
| Does the M9F9520 exist?                        | Confirmed                     |
| Is ZXW connected to its distribution?          | Confirmed                     |
| Is there a professional development ecosystem? | Yes, Masses Chip lists tools  |
| Is your SDC32K actually an M9F9520?            | Strong candidate, unconfirmed |
| Public M9F9520 datasheet and pinout?           | Not located                   |
| Verified instruction-set match?                | Not established               |
| Can stock firmware be read back?               | Unknown                       |
| Can it be reflashed through J1?                | Unknown                       |
| Is protected firmware recoverable?             | Unknown                       |

Your firmware notes identify the two-word startup sequence `df LL f0 HH`. Masses Chip's published documentation for other MCUs includes proprietary assembly instructions, making an instruction-set comparison worth pursuing. However, I found no verified opcode encoding for the M9F9520, so I can't claim that the sequence matches.

## Most useful next move: contact the manufacturer

Masses Chip — IC designer — 合肥磐芯电子有限公司 — cs@masses-chip.com — [Official contact page](https://www.masses-chip.com/contactus?utm_source=chatgpt.com)

ZXW Microchip — Supplier — 深圳市卓芯微半导体有限公司 — [MCU catalogue and contact details](https://zxw-chip.com/article/7?utm_source=chatgpt.com)

I'd specifically ask for the M9F9520 datasheet, instruction-set documentation, the compatible ZC-Writer hardware/software, J1 programming connections, code-protection details, and whether firmware readback is possible.

## What this means for your controller project

This research has made custom firmware materially more plausible. We now have a specific MCU family and a likely original chip designer rather than just an unidentifiable SDCX-marked component.

However, I wouldn't attempt firmware patching or replacement until we can back up the existing program or obtain a known-good factory image and recovery method. The manufacturer's related M9F951 explicitly supports programmable code protection, which is a warning that access to a programmer alone may not be sufficient.

For your immediate MIDI/OSC work, GLRA Studio and silent HID capture remain the lowest-risk route. For host-controlled individual RGB LEDs, I'd exhaust the stock HID protocol first, then consider the LED-chain intervention described in your notes.

My conclusion: the M9F9520 from Masses Chip/ZXW is now the leading candidate, supported by multiple independent clues. The decisive next evidence is its pinout, an instruction-set encoding match, or confirmation from the manufacturer that `SDC32K / 952CCU6` is an OEM-marked M9F9520.
