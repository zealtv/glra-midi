# Hackable Budget Macropads: Hardware and Firmware Survey

**Project context:** G-LRA K16_N3 MIDI/OSC controller (`grla`)  
**Research date:** 14 November 2026  
**Status:** Research and purchasing reference — not a validated compatibility list

## Objective

Identify inexpensive USB macropads, particularly models sold on AliExpress and Temu, suitable for conversion into flexible MIDI/OSC controllers. Two capabilities are being evaluated **separately**:

1. **Host-driven, addressable RGB without reflashing:** set the colour of individual LEDs dynamically using the device's existing firmware and a USB command/protocol. Ideally these writes affect RAM rather than wearing flash.
2. **Custom firmware potential:** identifiable MCU, development tools, access to a bootloader/programming interface, public source, and a credible recovery route.

Other desirable features: independent key/encoder input events, encoder pushbuttons, bank switching, USB MIDI or custom HID, bidirectional host feedback, macOS compatibility, and low cost.

**Important distinction:** a keyboard advertised as having "RGB", "programmable RGB", "VIA", or "QMK" does *not* necessarily support receiving arbitrary per-key LED values from a host on its stock firmware. Likewise, an addressable WS2812 chain is not evidence that the stock USB protocol exposes it.

## Executive summary

| Family / target | Typical controls | Per-key host RGB with stock firmware | Firmware potential | Assessment |
| --- | --- | --- | --- | --- |
| **SDCX / HCY-K006** | 6 keys + encoder | **Demonstrated** on specific hardware using vendor HID commands | Unclear; proprietary MCU | Best no-flash RGB reference |
| **SDCX / G-LRA K16_N3** (existing pad) | 16 keys + 3 clickable encoders | **Unverified** on exact pad; related SDCX commands exist | Unknown; SDC32K/952CCU6 identification incomplete | Continue protocol experiments first |
| **SDCX / HCY-K017 / GAMEKB-K17** | Larger keypad + dial/wheel | Community project reports per-key RGB | Unclear | Second SDCX reference |
| **WCH CH552 / CH552G generic pads** | Often 3–6 keys + encoder | **Usually unproven on stock firmware**; custom projects provide host RGB | **Good**, with documented examples and bootloader routes | **Flagged for future cheap, flexible hacking** |
| **Generic CH57x / `1189:884x`** | Often 12–15 keys + up to 3 encoders | Conflicting reports; older tested device appears limited to global colour | Revision-dependent and uncertain | Avoid buying for per-key RGB without exact proof |
| **DOIO KB16-01 rev 2** | 16 keys + 3 clickable encoders + OLED | Not established on stock firmware | **Strong**, QMK and community USB HID/MIDI SysEx extension | Best layout/firmware match |
| **KiiBOOM Cybrix 16** | 16 keys + 3 encoders | Not established on stock firmware | **Strong**, maker's QMK source | Good developer-friendly alternative |
| **Adafruit MacroPad RP2040** | 12 keys + encoder + OLED | Requires running suitable device-side software | **Excellent**, documented RP2040/CircuitPython | Reliable open development platform |
| **Pimoroni Keybow 2040** | 16 keys, no encoders | Requires running suitable device-side software | **Excellent**, documented RP2040/CircuitPython | Good RGB/button platform, missing encoders |

**Near-term recommendation:** retain the existing K16_N3 and test SDCX read-only colour capabilities; use HCY-K006 as a reference device if needed. For a purpose-built 16-key/3-encoder controller with firmware freedom, investigate **DOIO KB16-01 rev 2**. For a **cheap experimentation and future reusable firmware platform**, investigate **CH552/CH552G** pads, selected by exact PCB and MCU revision.

## 1. SDCX family: best evidence for no-flash host RGB

### HCY-K006

The [`parsaj-dev/sdcx-keypad`](https://github.com/parsaj-dev/sdcx-keypad) project reports tested host-controlled, individual-key lighting on an **HCY-K006**, USB ID `0816:246f`.

Reverse-engineered HID protocol operations described in the project include:

- `06 13 ...` — read per-key RGB table
- `06 12 ...` — write RGB colour table
- `06 14 03 ...` — set one key's colour

The device should be in its **Custom lighting mode (mode 5)** to prevent built-in animations overriding incoming colours. Host-driven dynamic effects have been demonstrated on the tested device.

**Caveat:** a successful RGB write does not by itself establish whether the target is volatile RAM or nonvolatile flash. Before sustained animation or long-term installation use, investigate write persistence and endurance. The project's support for numerous SDCX USB identities does not mean all physical layouts and LED indices have been verified.

### Existing G-LRA K16_N3

- 16 keys; 3 clickable encoders, yielding 25 configurable actions.
- Existing macOS research base: [`imolitor/glra-studio`](https://github.com/imolitor/glra-studio).
- Reverse-engineered SDCX lighting commands may be applicable, but **per-key host RGB has not been demonstrated on this exact model**.
- The MCU marked `SDC32K / 952CCU6` remains unconfirmed; **M9F9520** is a plausible lead, not an established identity. Do not assume pinout, programming protocol, flash readback, or firmware compatibility.

**Suggested tests, in order:** identify USB interfaces and firmware revision; back up settings; inspect supported lighting modes; attempt documented **read-only** RGB queries; map LED indices; only then evaluate carefully scoped colour writes and their persistence.

### HCY-K017 / GAMEKB-K17

[`dvdarkin/gamekb-k17`](https://github.com/dvdarkin/gamekb-k17) provides another reported example of per-key RGB programming on stock SDCX-family hardware. Useful as an independent comparison, but verify the exact board and USB identity before transferring commands.

## 2. CH552 / CH552G: future low-cost, flexible hacking candidate

> **Flag for future development:** CH552-based macropads are an attractive low-cost platform for custom USB MIDI/HID/OSC-bridge firmware and individually addressable RGB. This is primarily a **flash-once, then control from the host** strategy, **not** a demonstrated no-flash solution on anonymous stock boards.

### Why CH552 deserves attention

- WCH CH552/CH552G is a **known MCU family** rather than an unidentified vendor-marked controller.
- Small generic three-key and six-key devices with rotary encoders are widely advertised on Chinese marketplaces, often at the low-cost end of the category.
- Public community work shows custom firmware, raw HID communications, WS2812-compatible LED control, and recovery/programming workflows on **specific** boards.
- This makes it practical to define our own compact bidirectional protocol: key press/release, encoder deltas/buttons, bank status, and host-to-device per-LED RGB writes.
- A firmware build could expose **native USB MIDI** or raw HID; OSC itself would typically be supplied by a Mac-side bridge.

### Prior art

| Project | Relevant contribution |
| --- | --- |
| [`denniswjpg/padkit`](https://github.com/denniswjpg/padkit) | Custom firmware for a six-key/encoder pad; host-side configuration/feedback concepts |
| [`iamvaleriofantozzi/Tastierino`](https://github.com/iamvaleriofantozzi/Tastierino) | Three-key board with live independent LED control and custom HID; documents flashing considerations |
| [`Selta/CH552_macropad`](https://github.com/Selta/CH552_macropad) | CH552-based macropad firmware, WS2812 LEDs and physical wiring notes |
| [`perkinsb1024/CH552-macropad`](https://github.com/perkinsb1024/CH552-macropad) | Alternative firmware on a cheap three-key plus encoder pad |
| [`C0mpl3t3N00b/c3-touchkey-keyboard`](https://github.com/C0mpl3t3N00b/c3-touchkey-keyboard) | Commodity keypad firmware and bootloader/hardware access reference |

### What to verify before buying

1. Seller or community teardown confirms **actual chip marking `CH552` / `CH552G`**; avoid relying on vague tags such as “CH57x”.
2. **Exact PCB revision** matches a GitHub implementation, including switches, encoder pins, LED type and LED data pin.
3. Bootloader entry and flashing procedure are documented; ideally no destructive board surgery is required.
4. Individual LEDs really are **addressable**, not a single common RGB backlight.
5. Board exposes enough GPIO and USB functionality for the intended inputs/LED count.
6. If restoring original behaviour matters, determine whether a factory image is available; do not assume readback is possible.

**Proposed future experiment:** buy two identical, documented CH552 boards. Preserve one as a reference; flash the other with minimal test firmware implementing (a) button/encoder events, (b) a command to set any LED by index/RGB value, and (c) a simple USB MIDI or raw-HID endpoint. Keep mappings, banks and OSC in the host software initially.

## 3. Generic CH57x / `1189:884x`: abundant but inconsistent

Relevant research:

- [`kriomant/ch57x-keyboard-tool`](https://github.com/kriomant/ch57x-keyboard-tool)
- [`jvspier/macropad-rebind`](https://github.com/jvspier/macropad-rebind) and its [protocol notes](https://github.com/jvspier/macropad-rebind/blob/main/docs/PROTOCOL.md)
- [`fabiodalez-dev/MacroPadStudio`](https://github.com/fabiodalez-dev/MacroPadStudio)

These cheap boards are often identified by USB IDs such as `1189:8840`, `1189:8842`, or `1189:8890`, and may use a vendor-defined USB protocol to program keys, encoders, layers and lighting effects.

**Critical limitation:** community projects disagree about individual LED control. In particular, detailed protocol experiments on at least one `1189:8842` device found no usable host command to set individual key colours, despite internally addressable LED effects. Claims for other revisions should not be extrapolated.

**Buying stance:** not a preferred target for the present RGB requirement until the exact revision has a demonstrated live per-key USB protocol or documented replacement firmware path.

## 4. DOIO KB16-01 rev 2: best direct match for controller layout

- 16 keys, 3 clickable encoders, OLED and RGB.
- Rev 1 and rev 2 have different MCUs; **revision matching is essential**.
- Rev 2 is documented with an APM32F103CBT6 and QMK support.
- [`holofermes/orba-doio`](https://github.com/holofermes/orba-doio) adds host-addressable individual LEDs through **raw HID** and **USB MIDI SysEx**, plus OLED updates, on rev 2 firmware.

Illustrative SysEx example from the community project:

```text
F0 7D 4F 01 <led> <r> <g> <b> F7
```

**Note:** the live RGB capability is delivered by **replacement firmware**, not established on stock firmware. Verify firmware revision, source/build, bootloader and recovery route before flashing. Community proof-of-concept ≠ independently validated production support.

References:

- [Orba DOIO source](https://github.com/holofermes/orba-doio)
- [DOIO KB16-01 product](https://www.uikobo.com/products/doio-kb16-01-macro-keyboard-16-keys-3-knob-macro-pad)

## 5. KiiBOOM Cybrix 16: manufacturer-sourced QMK

The Cybrix 16 has 16 keys, three knobs and individually addressable WS2812 hardware. The manufacturer publishes [QMK-related source](https://github.com/KiiBOOM-Official/cybrix16), describing an STM32F103-based design with RGB matrix support.

**Strength:** published board-level firmware is a far better foundation than unidentified anonymous silicon.

**Limit:** hardware-addressable RGB and VIA/QMK support are **not** proof that the stock firmware receives live per-key host RGB. A custom raw-HID or MIDI feedback extension may still be necessary.

- [Product page](https://www.kiiboom.com/products/kiiboom-cybrix-16)

## 6. Open RP2040 alternatives

### Adafruit MacroPad RP2040

12 keys, one encoder, OLED, 12 addressable LEDs. Strong documentation and CircuitPython examples, including native USB MIDI. A good known-good development platform, although it has fewer encoders than the target design.

- [Official MIDI guide](https://learn.adafruit.com/adafruit-macropad-rp2040/macropad-midi)
- [Hardware source](https://github.com/adafruit/Adafruit-MacroPad-RP2040-PCB)

### Pimoroni Keybow 2040

16 keys and individually controlled RGB with RP2040/CircuitPython; **no encoders**. Useful for a keyboard-and-lighting prototype.

- [Australian supplier example](https://core-electronics.com.au/pimoroni-keybow-2040-tactile-keys.html)

## 7. Other reusable software ideas

- [`dozzenn/knurl`](https://github.com/dozzenn/knurl) — host-side macropad configuration ideas.
- [`SRGBmods/QMK-Binaries`](https://github.com/SRGBmods/QMK-Binaries) — host-controlled RGB/QMK integration references; device-specific compatibility required.
- [`imolitor/glra-studio`](https://github.com/imolitor/glra-studio) — current device's macOS SDCX protocol and configuration implementation.

## 8. Buying strategy and verification checklist

**Suggested order:**

1. **Do not replace the existing K16_N3 yet.** Test the documented SDCX colour queries and determine whether the pad supports a custom LED mode.
2. **Consider one verified HCY-K006** as a stock-firmware RGB protocol comparison.
3. **Shortlist a documented CH552 board** for inexpensive, future custom firmware work; preferably buy two of the same revision.
4. If a complete 16-key / three-encoder controller is the immediate objective, select a **DOIO KB16-01 rev 2** or **KiiBOOM Cybrix 16**, accepting a one-time firmware modification for full host feedback.

Before buying any anonymous AliExpress/Temu listing, ask for:

- Photo of the **front and back of the PCB**, including an in-focus MCU marking.
- USB **VID:PID** and product string (a screenshot from Device Manager or USB information is sufficient).
- Exact **PCB revision** and whether subsequent orders ship the same board.
- Whether each LED can be given a **different colour live from the computer**, not merely a saved lighting preset.
- Firmware/bootloader/backup availability, plus evidence of the original configuration utility.

**Prices and availability:** earlier survey price ranges are approximate, time-sensitive marketplace observations; they are intentionally omitted as firm quotations here. Confirm current pricing, shipping to Australia and PCB revisions before ordering. Temu/AliExpress listing photos and generic product titles are especially unreliable evidence of MCU identity.

## 9. AliExpress search terms

Search broadly first, then narrow to a documented chip/board. Use **both English and Chinese** terms; generic listings may omit the MCU designation entirely.

### Best terms for CH552 experimentation

```text
CH552 macropad
CH552G macro pad
CH552 3 key 1 knob
CH552 6 key rotary encoder
CH552G RGB mechanical keypad
CH552 USB programmable keypad
CH552 WS2812 macropad
CH552G 三键 旋钮 宏键盘
CH552 6键 旋钮 小键盘
CH552 可编程 小键盘 RGB
CH552 WS2812 键盘
```

### SDCX / host RGB references

```text
HCY K006 keypad
HCY K006 RGB macro keyboard
SDCX 6 key knob keypad
SDCX programmable keypad RGB
SDINNOVATION macro keypad
G-LRA K16 N3
GAMEKB K17 macro keyboard
```

### QMK / 16-key, 3-encoder candidates

```text
DOIO KB16-01
DOIO KB16-01 rev 2
DOIO 16 key 3 knob QMK
KiiBOOM Cybrix 16
16 key 3 knob QMK macropad
STM32 QMK RGB macropad
RP2040 macro pad rotary encoder RGB
```

### Broad discovery / Chinese marketplace terms

```text
programmable macro keypad per key RGB USB
USB macropad addressable RGB encoder
6 key 1 knob mechanical macro keypad
12 key 3 knob RGB macropad
16 key 3 encoder RGB macro keyboard
自定义 宏键盘 RGB 旋钮
可编程 小键盘 独立 RGB 灯
三旋钮 16键 宏键盘
```

**Search caution:** `CH57x`, `CH552`, `CH552G` and other WCH part numbers are not interchangeable. A seller matching an English keyword is not confirmation of the actual MCU or its firmware.

## 10. Next experiments for `grla`

- [ ] Make the G-LRA K16_N3 silent as a macOS keyboard and log all 25 actions (separate host-side milestone).
- [ ] Add read-only HID inspection of the K16_N3 lighting mode and RGB table.
- [ ] Determine whether the K16_N3 has distinct LED indices and a custom live-colour mode.
- [ ] Test host-to-device colour updates conservatively; establish whether writes affect RAM or flash.
- [ ] Investigate CH552 pads matching one of the documented community board layouts.
- [ ] Define a minimal portable device protocol: input events, bank, set LED RGB, get capabilities.
- [ ] Reassess firmware replacement only after verifying backup/recovery for each target MCU.

---

**Evidence standard:** “demonstrated” means reported in the linked project for a named device/revision, not independently tested here. “Possible” and “unverified” denote hypotheses requiring hardware tests. Do not infer cross-model command compatibility from appearance, USB family, or protocol similarities alone.
