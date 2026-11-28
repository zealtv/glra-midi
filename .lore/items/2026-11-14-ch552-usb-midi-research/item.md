# CH552 USB MIDI firmware research

An incoming research note dated 2026-11-14 collects CH552G native USB MIDI, incoming MIDI and addressable RGB firmware references for a possible future macropad experiment.

## Source

Received as `ch552-usb-midi-research.md` in the repository nest; author and research method were not supplied. Captured unchanged on 2026-11-14. Linked repositories and technical claims were not independently verified during intake.

## Relationship and limits

Follow-on material to lore:2026-11-14-macropad-hardware-survey. The note identifies `chrisssstos/2button-pad-hack` for reported native MIDI on a two-button board, `mimuz/mimuz-ch55x` for incoming and outgoing MIDI, `rgwan/ch55x_usbmidi` for transport, and `eccherda/ch552g_mini_keyboard` and `iamvaleriofantozzi/Tastierino` for hardware/RGB references.

The source explicitly identifies an integration gap: it found no single ready-to-flash implementation combining native MIDI, three keys plus encoder, and inbound per-LED RGB on the exact proposed board. Its CC-to-RGB protocol and staged experiment are proposals. Claims about bootloader recovery, firmware backup limitations, GPIO mappings and volatile lighting require verification against the actual MCU, PCB and implementation before use.

This is alternative-hardware research, not new evidence about the existing K16_N3 MCU or its firmware. It does not supersede glean:k16n3-firmware-replacement or glean:k16n3-lighting, nor change the current host-side MIDI implementation or its dependencies.

No purchase, flashing, implementation or resumption of parked work was authorised by this intake. No new stitch or glean guidance was created.

## Tags

- CH552
- USB-MIDI
- alternative-hardware
- firmware
- RGB
- unvalidated-reference
