# led-modes — step through the firmware's lighting modes and their settings

**Needs Bob at the pad.** Suggested model: Opus. Asked for by Bob, 2026-11-13.

Bob wants to see each stock animation (modes 1–11) and learn what we control:
brightness, speed, direction, fixed colour/HSV. Every `06 0b` persists to flash
(`glean:k16n3-lighting`), so budget about 20 writes in total, show Bob each new
packet before sending, and restore at the end (and on error).

1. Desk first: re-read the vendor configurator's K16_N3 layout file (public,
   `sdcx-tech.com`; nothing of it saved in the repo) for each mode's flags
   (brightness / speed / direction / colour honoured) and value ranges.
2. Probe script: `../led-probe*/probe.py` plus a `light <11-byte hex>` command,
   validated against those ranges, copied beside this file.
3. At the pad: each mode at its defaults (`06 16` gives `01 00 <mode> 04 03 03 00 08 ff ff ff`
   for every mode 1–11 on fw 103, read 2026-11-13); Bob describes it. Then
   a handful of setting changes on modes that honour them.
4. Mode 5 (up-down flow) and 4 (left-right flow) also test Bob's orientation
   reading: the vendor seems to intend encoders on the right (`loom:orientation`).
5. Restore `0100040403030008ffffff`; verify twice.

Record in `findings.md` beside this file; update `glean:k16n3-lighting`.
