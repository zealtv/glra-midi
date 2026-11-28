# Budget macropad hardware and firmware survey

An incoming research survey dated 2026-11-14 collects alternative macropad and firmware leads, retained as an unvalidated purchasing and research reference.

## Source

Received as `macropad-hardware-survey.md` in the repository nest; author and research method were not supplied. Captured unchanged on 2026-11-14. Linked projects have not been independently checked during this intake.

## Reading caveats

The survey distinguishes stock-firmware host RGB from replacement-firmware potential, and highlights exact PCB/MCU revision matching. CH552/CH552G, DOIO KB16-01 rev 2 and KiiBOOM Cybrix 16 are leads, not validated compatibility or purchasing recommendations from this repository.

Its K16_N3 assessment and proposed experiments lag the repository's recorded 2026-11-12/13 work:

- `glean:k16n3-hid-interfaces` records firmware 103, interfaces and 25 unique input codes; the MIDI MVP and silent keyboard operation are already implemented.
- `glean:k16n3-lighting` records demonstrated per-key RGB on this exact pad in Custom mode 12, read-only RGB inspection, and colour/mode writes surviving power cycles. No RAM lighting path was found; do not infer safe live animation from this survey's related-device examples or mode 5 reference.
- `glean:k16n3-firmware-replacement` retains the unconfirmed M9F9520 lead and backup/recovery limitations. This survey supplies no new datasheet, pinout, readback evidence or silicon identification.

The source's proposed purchases, protocol design and experiments are not authorisation to execute them. No new stitch was created, no parked work resumed, and no device writes were made during intake.

## Tags

- hardware-survey
- macropad
- CH552
- alternative-hardware
- unvalidated-reference
