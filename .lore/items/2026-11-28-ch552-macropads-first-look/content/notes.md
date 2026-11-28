# Two CH552G macropads: first look (2026-11-28)

Claude's record of a session with Bob on the evening of 2026-11-28. Bob had bought
two cheap macropads as better candidates than the K16_N3 for custom firmware, and
asked whether bidirectional MIDI could work on them: keys sending Note On/Off, the
encoder sending relative CC, and incoming MIDI setting the LEDs' colours.

## The boards

| | 3-key pad | 6-key pad |
|---|---|---|
| Label on case | "Keypad", model `3KV1`, DC 5V, Shenzhen Xiaozhi Technology Co., Ltd. | (not photographed) |
| Layout | 3 keys in a row, one encoder | 6 keys in two columns of three, one encoder |
| MCU | `WCH CH552G`, SOP-16, silkscreen `U7` (photo) | `WCH CH552G`, silkscreen `U7` (photo) |
| Sockets | hot-swap | hot-swap |
| LEDs | a window at each key; Bob saw them light briefly at plug-in, 2026-11-28, and judged them addressable | a window at each key (photo) |
| Unpopulated parts | resistor footprints by the chip (R10, R12, R16, R17 on the silkscreen; Bob, 2026-11-28: only **one** of these is actually unpopulated, correcting Tengu's photo note); D2/D3 near USB-C | `SW2`, a small push-button footprint next to the chip |
| Bootloader button | none found | none populated |

Chip markings were read off the photos and could be misread. The board with the
chip close-up (`photos/three-key-macropad-photo/`) is the 3-key board: it shows a
single row of sockets, and the resistor-pad photo shows the same footprint group.

## USB probes (read-only)

Both pads were probed in turn on Bob's Mac, plugged in through a USB-C to USB-A
cable (the first cable tried gave no USB connection at all). The probes used the
OS enumeration cache, standard `GET_DESCRIPTOR` requests (device, configuration,
HID report) and `GET_STRING`. Nothing was written to either pad. Raw output and
the script: `probes/`.

Both pads gave identical results:

- USB ID `1189:8890`, USB 1.1 full speed, 100 mA, one configuration, no string
  indexes in the device descriptor.
- Asking for strings by index anyway returns `1` = `wch.cn`, `2` = `CH559`,
  `3` = `key552` (4 and 5 return junk). This suggests firmware derived from WCH's
  keypad example code; `key552` fits the CH552G marking.
- Four HID interfaces:
  - 0: boot keyboard, report ID 1 (modifiers + 6 keys; lock-light output).
  - 1: vendor page `0xFF00`, report ID 3, 64-byte input and output; one
    interrupt **OUT** endpoint only. Probably the configuration channel used by
    the vendor's "MINI KeyBoard" style app. macOS attaches no driver to it.
  - 2: keyboard (report ID 1) plus consumer control (report ID 2, 16-bit usages
    up to `0x2FF`).
  - 3: boot mouse (3 buttons, X, Y, wheel).
- macOS refused to open the keyboard interfaces from the shell, so key presses
  weren't watched.

`1189:8890` is shared by many unrelated "MINI KeyBoard" pads. The 2026-11-14
survey (`lore:2026-11-14-ch552-usb-midi-research`) warns that the ID alone
doesn't identify the chip. Here the photos and the `key552` string both point to
CH552.

## Bootloader attempts on the 6-key pad

Goal: see whether the CH552's ROM bootloader (expected USB ID `4348:55e0`) can be
entered without board modification.

- ~20:02 and 20:06: Bob plugged the 6-key pad in with `SW2`'s two pads bridged.
  Both times it enumerated as the stock keypad, `1189:8890`. The bootloader never
  appeared. (The watcher for the first attempt had a bug; pyusb confirmed the
  stock ID afterwards. The second attempt was logged correctly: unplug 20:04:56,
  `1189:8890` at 20:06:12.)
- So `SW2` either doesn't connect the boot pin, or bridging it doesn't provide
  the condition the bootloader checks. Not yet traced with a meter.

## Outside evidence (web search, 2026-11-28; not verified on these boards)

- hackaday.io project 189914 (a CH552G 3-key + encoder pad, likely the same
  family) reports that the stock firmware needed **P1.5 shorted to GND** while
  plugging in for the first flash. A pull-up from D+ to 3.3 V did not work there.
  "Pulling pin 3 to ground" worked (P1.5 is pin 3 on the CH552G). After the
  custom firmware was installed, holding key 1 while plugging in entered the
  bootloader.
- `colons/3k1k` (firmware for the same family) says "the old firmware" enters the
  bootloader when the key furthest from the knob is held while plugging in. It's
  unclear whether "old firmware" means stock or an earlier custom build.
- `ch57x-keyboard-tool` supports `1189:8890` for key programming. Its LED
  commands list `8840`/`8842`/`8850`, not `8890`.
- Claude recalls a CH552G pinout with GND on pin 14 (across the chip from pin 3),
  5 V on pin 15 and 3.3 V on pin 16. That's from memory, not checked against the
  datasheet.

## Direction and next tests

Bob, 2026-11-28: "i'm not interested in middleware for these. only interested in
flashing potential." Host-side HID-to-MIDI for these pads is therefore out of
scope. These pads matter only as custom-firmware targets (native USB MIDI in and
out, LED colours set from MIDI and held in RAM).

Bob said he would try these later, cheapest first:

1. Hold each key, then the encoder push, while plugging in, starting with the key
   furthest from the encoder, on both pads. Look for `4348:55e0`.
2. With a meter on the unplugged pad, trace `SW2`'s pads (6-key) and the
   unpopulated resistor footprint (3-key) to the chip's pins: 3 (P1.5), 6 (RST),
   14 (GND) and 16 (3.3 V), once the pinout has been checked against the
   datasheet.
3. If neither works, momentarily short pin 3 (P1.5) to GND while plugging in, as
   hackaday 189914 did, keeping clear of the 5 V pin next to GND.

Caveats carried from the 2026-11-14 research: the WCH bootloader offers no normal
way to back up the stock firmware, so the first flash is one-way. Claude recalls a
low code-flash erase endurance for the CH552 (on the order of hundreds of cycles),
not yet checked against the datasheet.
