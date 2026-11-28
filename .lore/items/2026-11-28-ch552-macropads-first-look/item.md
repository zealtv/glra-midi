# Two CH552G macropads: photos, USB probes and first bootloader attempts (2026-11-28)

Bob's photos of two cheap CH552G macropads (a 3-key `3KV1` and a 6-key, each with an encoder), with metadata stripped, plus Claude's read-only USB probes of both and the first `SW2` bootloader attempts, kept as a first look at their custom-firmware potential.

## Source

Four Tengu inbox items Bob sent on 2026-11-28:
- `tengu--three-key-macropad-photo--20261128`: CH552G close-up
- `tengu--three-key-macropad-label-photo--20261128`: case label
- `tengu--three-key-macropad-resistor-pads--20261128`: whole board
- `tengu--six-key-macropad-photo--20261128`: whole board

Each photo sits under `content/photos/<item>/` with Tengu's `request.md`. Claude
stripped all embedded metadata with `exiftool -all=` before keeping. Telegram had
already removed camera EXIF; only a JFIF header and an sRGB profile remained.

`content/probes/` holds the raw probe output for each pad and the pyusb script
used. `content/notes.md` holds Claude's session record: the board table, the
decoded descriptors, the bootloader attempts, outside evidence, Bob's direction
and the next tests.

## Limits

- Chip markings were read off photos.
- Tengu's resistor-pad note names four unpopulated footprints (R10, R12, R16,
  R17). Bob corrected this the same evening: only one is unpopulated. The kept
  `request.md` is unchanged; `notes.md` carries the correction.
- Bootloader-entry claims from hackaday 189914 and `colons/3k1k` concern a
  similar board, not these exact PCBs.
- Nothing was written to either pad.

Follows lore:2026-11-14-macropad-hardware-survey and
lore:2026-11-14-ch552-usb-midi-research. These pads are separate from the K16_N3
and don't change `glean:k16n3-firmware-replacement`.

## Tags

- CH552
- macropad
- alternative-hardware
- firmware
- bootloader
- USB-probe
- photos
