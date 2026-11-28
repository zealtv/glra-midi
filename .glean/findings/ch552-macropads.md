# Bob's two CH552G macropads matter only as firmware targets; the stock bootloader route isn't found yet

When working with the 3-key `3KV1` or 6-key CH552G pads, `1189:8890`, `key552`, the WCH bootloader `4348:55e0`, `SW2`, or flashing a cheap macropad: Bob wants flashing potential only, no middleware (2026-11-28), and as of that evening no way into the bootloader had been found without a hardware short.

## Triggers
- 3KV1
- CH552
- CH552G
- key552
- 1189:8890
- 4348:55e0
- SW2
- P1.5
- six-key
- three-key

## Context
From the 2026-11-28 session (`lore:2026-11-28-ch552-macropads-first-look`, `content/notes.md`):
- **Direction:** Bob, 2026-11-28: "i'm not interested in middleware for these. only interested in
  flashing potential." Don't propose host-side HID-to-MIDI for these pads. The goal is our own
  firmware: native USB MIDI in and out, LED colour from MIDI held in RAM.
- **Hardware (photos):** both boards carry a `WCH CH552G` (`U7`), hot-swap sockets, an encoder and
  LED windows at each key. Bob saw the LEDs light at plug-in and judged them addressable. 6-key:
  unpopulated push-button footprint `SW2` beside the chip. 3-key: one unpopulated resistor footprint
  among R10/R12/R16/R17 (Bob's correction of Tengu's "four").
- **Stock firmware (read-only USB probe, both pads identical):** `1189:8890`, USB 1.1. Strings by
  index: `wch.cn`, `CH559`, `key552`. Four HID interfaces: boot keyboard, vendor `0xFF00`
  out-only config channel (report ID 3, 64 bytes), keyboard + consumer, boot mouse. No MIDI, no live
  LED channel.
- **Bootloader:** bridging `SW2` while plugging in gave the stock `1189:8890` twice, never
  `4348:55e0`. Untried as of 2026-11-28: holding each key while plugging in, a meter trace of `SW2`
  and the resistor pad, and the P1.5 (pin 3) to GND short that hackaday 189914 used on a similar
  board. The pinout (GND 14, 5 V 15, 3.3 V 16) comes from memory and hasn't been checked against
  the datasheet. Keep clear of shorting 5 V.
- **Device safety:** Bob does the physical steps. No flashing without his OK for that step. The
  stock firmware can't be backed up through the WCH bootloader (2026-11-14 research), so the first
  flash is one-way.
- To watch for the bootloader on macOS, poll pyusb/libusb for `4348:55e0`. Pair `idVendor` and
  `idProduct` per device: a line-based `ioreg` parse mispaired them on 2026-11-28.

## Associations
- [[k16n3-firmware-replacement]]
- [[the-repo-is-a-map-not-the-territory]]
