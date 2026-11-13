# custom-firmware — our own LED control on the pad, by firmware or hardware (parked)

Bob, 2026-11-13: "let's move firmware-approaches into it's own custom-firmware
thread. for the moment we will accept using the factory firmware led modes and
continue with the app creation." (`lore:2026-11-13-config-app-brief`)

Parked (`.waiting`) the same day: nothing here runs until Bob resumes it
(`./.loom/loom.sh resume custom-firmware`). Not on the queue.

What it would give: live per-key LED control without flash wear, which the
dropped `rgb-feedback` goal wanted (per-key colours, host animations, LED
feedback for toggles and incoming MIDI). `loom:backlog` (`osc-io`,
`midi-feedback`) waits on this thread at Bob's request.

Where things stood on 2026-11-13:
- `glean:k16n3-firmware-replacement`: the desk study found no practical way to
  put our own firmware on the stock MCU; no backup is possible yet.
- `glean:k16n3-lighting`: every lighting write on stock firmware persists to flash.
- `firmware-approaches` (child): the four candidate routes and the chip lead
  (`lore:2026-11-13-mcu-chip-lead-m9f9520`).
- Evidence from the dropped thread: `.loom/dropped/rgb-feedback/*.tied/`.

Device safety (brief §9) still applies: no firmware, bootloader or reset
commands, and nothing connected to `J1`, without Bob's OK for that specific step.
