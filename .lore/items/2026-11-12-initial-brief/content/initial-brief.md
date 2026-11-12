# G-LRA K16_N3 — MIDI / OSC Controller

## Project specification

**Status:** Planning  
**Platform:** macOS  
**Hardware:** G-LRA K16_N3 USB macropad  
**Approach:** Host-side HID middleware, retaining stock firmware

## 1. Overview

Develop a lightweight macOS application that transforms the G-LRA K16_N3 USB macropad into a flexible, bidirectional MIDI and OSC controller.

The device has:

- 16 programmable keys
- 3 rotary encoders, each with push-button functionality
- RGB lighting
- USB HID connectivity
- An existing proprietary configuration interface

The device currently presents itself as a USB keyboard. Rather than replacing its firmware, we will intercept its input at the macOS HID level and translate it into MIDI and OSC.

The application must prevent the device from generating ordinary macOS keyboard input while it is operating.

Use the open-source **GLRA Studio** project as the starting point, reusing its device identification, HID protocol implementation, configuration and lighting functionality where practical.

**Reference project:**  
https://github.com/imolitor/glra-studio

## 2. Primary goals

1. Capture all physical inputs without allowing keystrokes to reach macOS applications.
2. Expose the device as a configurable MIDI controller.
3. Support sending and receiving OSC messages.
4. Implement software-defined banks, mappings and parameter states.
5. Support bidirectional communication, including MIDI/OSC feedback.
6. Control the device's RGB lighting from the host, including parameter and bank feedback where supported.
7. Keep the implementation lightweight, modular and extensible.

Prefer existing libraries and the GLRA Studio implementation over developing a new protocol from scratch.

No firmware modification should be necessary.

## 3. Phase 1 — Silent HID capture and event logging

**This is the immediate development milestone. Do not implement MIDI, OSC, banking or advanced lighting yet.**

### 3.1 Exclusive HID access

Use macOS IOKit to capture the device exclusively.

Investigate:

- `IOHIDManager`
- `IOHIDDeviceOpen`
- `kIOHIDOptionsTypeSeizeDevice`
- HID input reports and callbacks

The intended approach is to identify the macropad and seize its keyboard HID interface so that its reports are received by our application rather than the normal macOS input system.

Important requirements:

- Capture this specific device only.
- Preserve normal operation of all other keyboards.
- Avoid global keyboard hooks where possible.
- Do not rely on application focus.
- Do not simply use obscure shortcuts such as F13–F24 without interception.
- Investigate macOS Input Monitoring permissions and any restrictions on exclusive device access.
- Do not silently fall back to ordinary keyboard capture if exclusive access fails.

The exact HID interface layout must be inspected. Keyboard input and vendor-specific configuration may use separate HID interfaces.

Apple API reference:  
https://developer.apple.com/documentation/iokit/1588670-iohiddeviceopen

### 3.2 Hardware identification

GLRA Studio identifies the tested hardware as:

- Device: `G-LRA k16_n3`
- USB VID:PID: `36ae:2475`
- Internal PID: `246d`
- Tested protocol: Version 1
- Tested firmware value: `100`

Verify the connected device's actual descriptors before assuming compatibility.

GLRA Studio supports reading and writing the 16 key assignments and all nine encoder actions.

### 3.3 Input mapping

There are 25 independently programmable actions:

| Physical control | Logical events |
|---|---|
| Keys 1–16 | Press / release |
| Encoder 1 | Clockwise / counterclockwise / push |
| Encoder 2 | Clockwise / counterclockwise / push |
| Encoder 3 | Clockwise / counterclockwise / push |

Configure each of the 25 actions to emit a unique keyboard assignment using GLRA Studio.

The middleware will translate these assignments into logical events.

**Important:** The existing firmware does not necessarily expose physical control IDs directly. Distinct physical controls with identical assignments can generate indistinguishable HID reports. Therefore, unique assignments and an explicit mapping are required.

Verify whether key releases and encoder-button releases can be distinguished reliably. Preserve actual press/release semantics rather than synthesizing them without justification.

### 3.4 Terminal logging

Develop a minimal CLI application that:

1. Finds the connected macropad.
2. Opens the appropriate HID interface exclusively.
3. Reads incoming input reports.
4. Decodes input into logical controls and actions.
5. Prints timestamped events to the terminal.

Example output (illustrative):

```text
[12:01:03.122] KEY 01 DOWN
[12:01:03.210] KEY 01 UP
[12:01:04.015] ENCODER 1 CW
[12:01:04.042] ENCODER 1 CW
[12:01:04.311] ENCODER 2 CCW
[12:01:05.107] ENCODER 3 BUTTON DOWN
[12:01:05.218] ENCODER 3 BUTTON UP
```

If release events cannot be reliably detected, report that limitation explicitly.

Optional verbose mode should print raw HID report bytes to support debugging.

### 3.5 Phase 1 acceptance criteria

- [ ] Device detected automatically.
- [ ] Exclusive HID capture works on the target Mac.
- [ ] All 16 keys individually identified.
- [ ] All 3 encoder push buttons identified.
- [ ] Clockwise and counterclockwise movement identified independently for each encoder.
- [ ] Press and release events logged wherever supported.
- [ ] No macropad keystrokes reach foreground applications while capture is active.
- [ ] Normal Mac keyboard remains fully operational.
- [ ] No firmware flashing required.
- [ ] Clean shutdown releases the HID device.
- [ ] Disconnect/reconnect handled safely.

**Milestone:** The macropad becomes completely silent as a keyboard while all its controls produce reliable terminal events.

## 4. Phase 2 — MIDI output

Extend the event system to expose a virtual CoreMIDI output.

Suggested libraries:

- `python-rtmidi`
- `mido`

Required functionality:

### Keys

Configurable actions including:

- MIDI Note On / Note Off
- MIDI CC
- Program Change
- Bank selection
- Toggle and momentary behaviour

Support configurable MIDI channel, note/CC number and velocity/value.

### Encoders

Support two primary modes:

**Relative CC**

- Clockwise emits an increment.
- Counterclockwise emits a decrement.
- Configurable relative MIDI encoding to suit the receiving application.

**Absolute CC**

- Maintain a software parameter value from 0–127.
- Increment/decrement this value with encoder movement.
- Emit the current absolute value.
- Restore the previous state when switching banks.
- Allow incoming feedback to update the parameter value.

Encoder buttons should be independently assignable.

## 5. Phase 3 — OSC

Add bidirectional OSC communication using a library such as `python-osc`.

Support configurable destination IP addresses, ports and OSC paths.

Illustrative outgoing messages:

```text
/key/1 1
/key/1 0
/encoder/1/delta 1
/encoder/1/delta -1
/encoder/1/value 85
/encoder/1/button 1
/bank 2
```

Support incoming OSC messages for:

- Parameter updates
- Bank changes
- LED colours
- Global lighting state
- Other configurable control feedback

Keep MIDI and OSC as independent output adapters to a common internal event and state system.

## 6. Phase 4 — Banks and mappings

Implement configurable software banks.

Each bank should define:

- Key assignments
- Encoder assignments
- MIDI channels and messages
- OSC mappings
- Parameter values
- Optional lighting configuration

Possible bank navigation:

- Encoder push button
- Dedicated key
- Incoming MIDI or OSC message

Banks should support independent parameter states.

A bank change must not generate unnecessary MIDI or OSC output unless configured to do so.

Support saving and loading configuration from a readable format such as JSON.

## 7. Phase 5 — RGB feedback

Use GLRA Studio's existing HID lighting protocol as the starting point.

**Confirmed on supported hardware:**

- Lighting on/off
- Steady colour
- Breathing mode
- Rainbow mode
- Global RGB colour

**Requires investigation:**

- Individual key LED control
- Host-driven dynamic colour updates
- Update frequency and latency
- Whether repeated writes affect persistent flash storage
- Whether lighting can be changed without disrupting input capture

Additional reference:

https://github.com/parsaj-dev/sdcx-keypad

This project documents more extensive SDCX-family lighting commands, including per-key host control on another macropad model. Compatibility with the K16_N3 must be established experimentally.

### Intended feedback examples

- Different colours for different banks.
- LED state representing toggled MIDI parameters.
- Colours updated by incoming OSC or MIDI.
- Parameter feedback indicating current application state.
- Optional dynamic lighting if safely supported.

Avoid high-frequency lighting writes until the storage and update mechanism is understood.

## 8. Software architecture

Suggested modules:

```text
G-LRA K16_N3
      |
      v
HID Input Driver
      |
      v
Event Decoder
      |
      v
Control / Bank / State Engine
      |
      +----> MIDI Output
      |
      +----> OSC Output
      |
      +<---- MIDI Input
      |
      +<---- OSC Input
      |
      v
Lighting / Feedback Engine
      |
      v
HID Configuration Interface
      |
      v
G-LRA K16_N3 RGB
```

Design principles:

- Prefer straightforward, minimal implementations.
- Maintain separation between hardware I/O and application logic.
- Use one consistent internal representation for control events.
- Do not couple MIDI/OSC handling directly to raw HID reports.
- Keep physical input configuration distinct from logical bank mappings.
- Avoid unnecessary background processes, polling and dependencies.
- Support a headless command-line runtime.
- Prefer reliable reconnection and recovery over complex UI features.

A GUI for mapping and configuration is a possible later enhancement, not an initial requirement.

## 9. Implementation notes and risks

### Existing GLRA Studio functionality

GLRA Studio is a Python / PySide6 macOS application with an existing HID protocol implementation.

Its input monitoring currently observes keyboard activity and does not prevent keystrokes reaching other applications.

The new implementation must provide an alternative, device-specific input capture path.

Reuse its existing configuration protocol and diagnostic code where appropriate. A minimal CLI may be preferable to extending its GUI initially.

The project is GPL-3.0-only; consider licensing obligations when reusing its code.

### Exclusive access

Exclusive HID seizure is the intended mechanism, but successful suppression must be verified on the target macOS version.

If access is restricted, investigate an alternative such as a device-specific Karabiner-Elements interception layer.

Avoid using ordinary global event taps as the final solution if they cannot reliably distinguish the macropad from the normal keyboard or prevent unintended shortcuts.

### Event reliability

Encoder rotations may be represented as brief keyboard press/release events rather than native relative values.

Test rapid rotation, simultaneous key presses, long holds and modifier interactions.

Prevent stuck MIDI notes by tracking press/release state and sending Note Off as appropriate when disconnecting, switching configurations or shutting down.

### Device safety

- Back up device configuration before modifying assignments.
- Avoid undocumented firmware-update or bootloader commands.
- Do not flash replacement firmware in this project.
- Avoid unverified writes to unknown device memory.
- Preserve a straightforward recovery path.

## 10. Development roadmap

### Milestone 1 — HID capture

**Implement this first.**

- Clone and inspect GLRA Studio.
- Identify relevant input and configuration interfaces.
- Establish exclusive macOS HID capture.
- Configure unique hardware assignments.
- Decode every control.
- Log events to the terminal.
- Verify complete suppression of normal keyboard input.

### Milestone 2 — MIDI

- Virtual CoreMIDI output.
- Note and CC mappings.
- Relative and absolute encoder modes.
- MIDI input feedback.

### Milestone 3 — OSC

- OSC output.
- OSC input.
- Configurable message mappings.

### Milestone 4 — Banks

- Software banks.
- Persistent parameter state.
- Configurable bank switching.

### Milestone 5 — Lighting

- Global RGB control.
- Bank feedback.
- Investigate individual key colours.
- Bidirectional MIDI/OSC lighting updates.

### Milestone 6 — Configuration

- Readable configuration files.
- Optional GUI.
- Reliable startup, shutdown and hotplug recovery.

## 11. Immediate task for coding agent

Start by examining:

https://github.com/imolitor/glra-studio

Understand its HID implementation, device detection, input monitoring and mapping functionality.

Create a minimal macOS CLI program that opens the G-LRA K16_N3 exclusively, suppresses its normal keyboard events and logs all 25 physical control actions, including release events where available.

Reuse existing GLRA Studio code wherever appropriate.

Do not implement MIDI, OSC or RGB feedback yet.

Prioritize a small, testable implementation and verify that the pad generates **no keyboard events in ordinary macOS applications** while captured.

Document any platform restrictions, permissions, protocol limitations or unresolved questions before progressing.

The immediate deliverable is a reliable, silent HID event logger that can serve as the foundation for the larger controller.