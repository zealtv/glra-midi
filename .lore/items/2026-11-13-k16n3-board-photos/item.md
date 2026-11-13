# K16_N3 board photos (PCB underside, 2026-11-13)

Six photos Bob took of his pad's opened PCB on 2026-11-13 for `firmware-feasibility`, kept whole as they arrived via Tengu.

## Source

Two Telegram albums Bob sent through Tengu on 2026-11-13
(`.nest/in/tengu-glra-osc-photos-20261113`, four photos;
`.nest/in/tengu-glra-osc-extra-photos-20261113`, two close-ups). Tengu's
`request.md` for each sits beside its photos.

## What the photos show (read by Claude on 2026-11-13; markings read off photos, may be misread)

- `album-1/source-4.jpg`: whole underside. 4×4 switch grid, each with a
  hot-swap socket and a 4-pin RGB LED (pins labelled `G`, `DI`, `DO`, `V`, so
  an addressable, WS2812-style daisy chain); silkscreen `LED1`–`LED16`,
  `S1`–`S16`. Three encoders along the top edge (in this underside view), USB-C
  (`TYPE_C1`) on the right edge, main chip `U1` above the grid.
- `album-1/source-3.jpg`: `U1` close-up. 48-pin quad package with an `SDCX`
  logo; marking reads roughly `SDC32K` / `952CCU6` / `4GA83 1201`. Probably a
  vendor-branded part; the vendor layout file names `mcu_type "9520"`.
- `album-1/source-2.jpg`: USB-C and nearby passives (`R5`–`R8`, `L8`, `C3`).
- `album-1/source-1.jpg`: lower-left switches and LEDs (`LED15`/`S14`, `LED16`/`S13`).
- `album-2/source-1.jpg`: board marking `SD014_K009_16Key_ARGB_V2.0`, `2026-6-17`, `231M`.
- `album-2/source-2.jpg`: `J1`, four through-hole pads labelled `GND SCK SDA VDD`.
  Possibly a debug/programming header (SWD-like) or I2C; not known.

## Tags

- hardware
- pcb
- mcu
- firmware
- led
