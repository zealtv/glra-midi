# re-prior-art — find other reverse-engineering work on this pad family (desk)

Suggested model: Sonnet. Desk only; no hardware. Asked for by Bob, 2026-11-13:
"another search for any other reverse engineering work we might be able to reference".

So far the repo leans on two outside sources: `../glra-studio` (peer repo) and
`parsaj-dev/sdcx-keypad` (MIT; HCY-K006 `0816:246f`). Look wider for anything
that documents the SDCX / G-LRA family or its parts:
- other projects, gists, forum or blog posts on SDCX-configured macropads
  (`sdcx-tech.com` configurator, USB VIDs `0816`, `36ae`, the K16/K006/K009
  names, the board marking `SD014_K009_16Key_ARGB_V2.0`), incl. AliExpress /
  Amazon resold variants under other brands;
- the HID config protocol (`06 xx` reports, `aa` replies), lighting, macros;
- the MCU: SDCX-branded `SDC32K 952CCU6` (marking read off a photo), vendor
  `mcu_type 9520` (also `951`, `9800`, `AT405` in the updater): what chip it
  really is, datasheets, open firmware ports (QMK/Vial/etc.);
- firmware dumps, update files (`update.json` in the configurator), bootloader notes.
For each source: URL, what it covers, licence, how trustworthy (tested on what
device, firmware), and which of our open questions it bears on. Write
`sources.md` beside this file. Save nothing copyrighted into the repo.
