# CH552 USB MIDI Firmware Research

**Project:** `grla` — future low-cost, flexible macropad hardware  
**Date:** 14 November 2026  
**Status:** Research / candidate for future development

## Summary

The **WCH CH552 / CH552G** is a promising low-cost microcontroller for turning inexpensive AliExpress-style macropads into native USB MIDI controllers. Several projects demonstrate replacement firmware, including one that has been flashed onto a real low-cost CH552G macropad and enumerates directly as a USB MIDI device.

The broader goal is a **bidirectional MIDI controller**: buttons and encoders send notes/CCs, while messages from the host control each RGB LED. The latter is feasible with custom firmware, but **no single ready-to-flash project was identified that combines native USB MIDI, the common three-key/one-encoder board, and inbound per-LED RGB feedback on that exact board**.

**Candidate status:** Keep CH552G on the `grla` hardware shortlist as a particularly cheap and flexible custom-firmware platform. Confirm the actual MCU and PCB revision before purchasing or flashing; sellers frequently omit the chip part number.

## 1. Native USB MIDI on a cheap CH552G macropad

### [chrisssstos/2button-pad-hack](https://github.com/chrisssstos/2button-pad-hack)

The most directly relevant prior work: custom firmware for a cheap two-button CH552G macropad (originally reported as USB `5131:2019`). The developer reports successful flashing and USB enumeration as a class-compliant **`MIDI Pad`**.

Documented features include:

- MIDI Note On and Note Off from physical buttons.
- MIDI Control Change messages, including momentary `127` / `0` values.
- Configurable MIDI channel, note numbers and CC numbers.
- A pin-discovery mode to help adapt firmware to other PCB layouts.
- macOS-oriented build, flashing and MIDI-monitoring tooling.
- A native USB MIDI 1.0 implementation in C, built with SDCC.

Documented setup and example commands:

```bash
brew install sdcc libusb
python3 -m venv venv
./venv/bin/pip install pyusb mido python-rtmidi

./venv/bin/python pad.py flash
./venv/bin/python pad.py monitor
```

**Important:** These are project-specific commands. The pad must first be in its supported bootloader mode; do not assume the flashing procedure works unchanged on a different CH552 board.

**Assessment:** Best starting point for native USB MIDI transport and a minimal button-to-MIDI implementation.

## 2. Bidirectional MIDI library

### [mimuz/mimuz-ch55x](https://github.com/mimuz/mimuz-ch55x)

A compact USB MIDI library for the **CH55xduino** environment (the Arduino-like CH55x development stack).

Reported message support:

| MIDI message | Send | Receive |
|---|---|---|
| Note On | Yes | Yes |
| Note Off | Yes | Yes |
| Control Change | Yes | Yes |
| SysEx | Not documented | Not documented |

Incoming note and CC callbacks make it suitable for **host-to-device feedback**, including LED control.

A minimal feedback experiment could dedicate three incoming CCs to red, green and blue channels, with a simple selection scheme for individual LEDs. This is an **implementation proposal**, not a claimed built-in RGB protocol. Each MIDI CC carries a 7-bit value (`0–127`), so the firmware would need to scale or combine values for 8-bit RGB output.

The repository includes examples and a reference board; review and replace the example USB VID/PID appropriately for any derivative firmware.

**Assessment:** Best reference for receiving MIDI as well as sending it.

## 3. Another low-level USB MIDI reference

### [rgwan/ch55x_usbmidi](https://github.com/rgwan/ch55x_usbmidi)

An SDCC-based **USB MIDI loopback** implementation for the CH55x family. Useful for studying USB descriptors, endpoint handling and MIDI packet exchange.

It is **not** a completed key-and-encoder MIDI controller; controller functionality was listed as future work.

**Assessment:** Transport reference, especially if implementing a custom USB stack.

## 4. Hardware mappings and addressable RGB on cheap three-key pads

Two projects cover the physical hardware and LED side of the common inexpensive **three-key / one-encoder CH552G RGB macropad**:

### [eccherda/ch552g_mini_keyboard](https://github.com/eccherda/ch552g_mini_keyboard)

Replacement firmware for a CH552G mini-keyboard. Relevant for discovering the GPIO assignments used by the keys, encoder and LEDs on a matching board.

### [iamvaleriofantozzi/Tastierino](https://github.com/iamvaleriofantozzi/Tastierino)

Demonstrates independently controlled RGB LEDs, bidirectional raw-HID communication, and runtime/volatile configuration changes on compatible CH552G hardware. Also documents macOS-oriented flashing work.

**Assessment:** Pair these hardware references with a MIDI transport project to build the desired controller. Hardware pinouts must be verified on the purchased PCB: similar-looking products may be wired differently.

## 5. Proposed MIDI/RGB controller architecture

```text
             CH552G macropad
       3 keys + encoder/button + RGB
                      |
            Native USB MIDI
                (two-way)
                      |
             Host application
          Reaper / Max / Pure Data
                      |
         Optional host MIDI–OSC bridge
```

### Device → host

- Keys: MIDI Note On when pressed, Note Off when released.
- Encoder clockwise/counterclockwise: relative MIDI CC increments/decrements.
- Encoder push-button: assignable MIDI note, CC or bank change.
- Optional local bank selection and per-bank assignments.

### Host → device

- Receive MIDI CC to change LED colour, brightness, state or bank.
- For an initial proof of concept, receive three CC values representing RGB channels for one LED.
- Later, consider MIDI SysEx or a separate raw-HID interface for compact per-LED RGB commands and richer state feedback.
- Keep dynamic LED updates **RAM-only**, without flash writes on every lighting change.

### Target behaviour

A class-compliant USB MIDI controller that **does not emit keyboard keystrokes**, requiring no keyboard-interception middleware on macOS. A host-side OSC bridge would remain optional; USB MIDI does not itself provide native OSC transport.

## 6. Flashing and recovery caveats

The CH552 includes a factory USB bootloader in mask ROM. On supported boards this provides a recovery route even if the application firmware fails, provided the bootloader can still be entered.

However:

- The standard bootloader **does not provide a normal method to back up the existing vendor application firmware**.
- First-time bootloader entry differs between boards. Some community projects describe board-specific USB D+ / 3.3 V boot-entry techniques; **do not apply those instructions blindly** to a different board.
- Identify the exact MCU, PCB revision and boot-entry pads before flashing.
- Follow a known working project for that specific board, ideally with a proven recovery procedure.
- A custom firmware could implement a convenient bootloader-entry gesture (for example, hold the encoder button during power-up).

Buying by appearance alone is risky. A product using **MINI KeyBoard V02.1.1** configuration software or USB ID `1189:8890` is *not necessarily* a CH552G device; this software and ID appear across differing controller hardware.

## 7. Suggested first experiment

Purchase a **three-key, one-encoder, WS2812-equipped CH552G** pad matching a public PCB teardown/firmware project.

Then implement in stages:

1. Confirm CH552G marking, PCB revision and GPIO mapping.
2. Verify bootloader entry and reliable flashing/recovery.
3. Flash minimal firmware that enumerates as a native USB MIDI device.
4. Send Note On/Off from all three keys and the encoder push-button.
5. Send relative CC messages for encoder direction.
6. Receive three MIDI CCs and update one RGB LED live in RAM.
7. Extend incoming RGB feedback to all LEDs and add banks.
8. Optionally add richer SysEx or raw-HID feedback and host-side OSC translation.

### Acceptance criteria for proof of concept

- Device appears as a class-compliant USB MIDI device on macOS.
- All keys and encoder actions work reliably.
- No normal keyboard input is emitted.
- Host can change an LED's RGB colour repeatedly **without reflashing**.
- LED updates do not persistently rewrite firmware/configuration flash.
- Device can be reliably re-entered into its bootloader and reflashed.

## 8. Project comparison

| Purpose | Recommended source |
|---|---|
| Native USB MIDI firmware | [2button-pad-hack](https://github.com/chrisssstos/2button-pad-hack) |
| Bidirectional MIDI | [mimuz-ch55x](https://github.com/mimuz/mimuz-ch55x) |
| USB-MIDI low-level implementation | [ch55x_usbmidi](https://github.com/rgwan/ch55x_usbmidi) |
| Three-key/encoder GPIO mapping | [ch552g_mini_keyboard](https://github.com/eccherda/ch552g_mini_keyboard) |
| Addressable LED and raw-HID control | [Tastierino](https://github.com/iamvaleriofantozzi/Tastierino) |

## Conclusion

CH552G deserves a place on the **future cheap, flexible hacking** shortlist for `grla`. Native USB MIDI has been demonstrated on real low-cost CH552G macropad hardware; bidirectional MIDI libraries and addressable RGB firmware also exist. Combining them for the common three-key/one-encoder RGB pad is a small but real integration project—not yet a turnkey firmware download for every AliExpress variant.

**Recommended next step:** obtain an exact-match CH552G RGB pad, verify its PCB against the public projects, and prove native MIDI plus incoming RAM-only RGB feedback before designing a larger controller around the chip.
