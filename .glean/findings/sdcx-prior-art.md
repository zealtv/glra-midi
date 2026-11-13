# Other repos document the SDCX pad family, but none covers the K16_N3 or names its MCU

When looking for outside protocol evidence, lighting persistence claims, or firmware/MCU information for the pad: as of 2026-11-13 four MIT-or-unlicensed repos read the same vendor WebHID bundle we do; only one tested persistence.

## Triggers
- sdcx-keypad
- gamekb-k17
- minikbconfig
- macropad-movil
- prior art
- update.json
- 16keysd
- SDC32K
- 9520

## Context
Found by the `re-prior-art` worker, 2026-11-13 (full list, trust ratings and
links: `.loom/dropped/rgb-feedback/re-prior-art.tied/sources.md`):
- `parsaj-dev/sdcx-keypad` (MIT; HCY-K006 `0816:246f`): driver + protocol notes;
  issue #4 is a G-LRA k6_n1 on `36ae:246f` (our vendor ID); issue #5: fw 106
  needs ~10 ms between chunked writes.
- `dvdarkin/gamekb-k17` (MIT; K17 `0816:0220`): the best-labelled protocol doc;
  its author **tested** that colour, lighting and keymap writes persist across
  replug with no save step, agreeing with `glean:k16n3-lighting`. Mode table
  differs per model.
- `kabuko/minikbconfig` (MIT; 3- and 6-key): HSV value < 32 doesn't light;
  a read-back of command `12` reportedly erased a key colour (more reason never
  to touch bulk `06 12`).
- `RiderDeck-8/macropad-movil` (no licence, so read only): key-action type table
  (`1F` light-control actions run in firmware on a key press).
- Vendor `www.sdcx-tech.com/update.json` (2026-11-13) has no `36ae_2475` entry;
  `0816_2475` maps to `16keysd_v105.bin`, which `firmware-feasibility` found to
  be a `951`-class image (wrong chip for Bob's `9520`). Updater table:
  `mcu_type 9520` = 30 KB user + 2 KB boot at `0x7800`, which fits the
  `SDC32K` marking. Never send firmware meant for another ID.
- None names the MCU, holds a firmware dump, or implements the update path;
  all refuse it. Some write it `06 55`/`06 5A`; the 2026-11-13 bundle sends
  `55 …`/`5a …` with no `06` prefix (`glean:k16n3-firmware-replacement`).

## Associations
- [[k16n3-lighting]]
- [[glra-studio-reuse]]
