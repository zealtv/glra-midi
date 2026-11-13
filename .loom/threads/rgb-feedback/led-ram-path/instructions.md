# led-ram-path — look for a non-persistent way to set per-key colour (desk)

Suggested model: Opus. Desk only; no hardware writes. Asked for by Bob, 2026-11-13.

`led-probe` found `06 14` and `06 0b` both persist across replug (fw 103),
which rules out live host animation on them. Look for a RAM-only path:
- Group-6 opcodes the configurator uses that `led-research` didn't identify:
  `07, 09, 0c, 0d, 40, 41, fb`. What each sends, what the UI does with it,
  and whether any is a preview / streaming / "direct" mode. (`0f` = factory
  reset; `55`/`5a` = firmware update: never send.)
- How the configurator previews colours while you drag a picker: does it call
  `06 14` per change, debounce, or something else?
- `parsaj-dev/sdcx-keypad`: issues, commits, or notes on whether per-key writes
  survive power cycles on HCY-K006 (it streams them at 20 fps).
- Bulk `06 12`: does anything suggest it goes to RAM? (Probably the same table.)
Write `research.md` beside this file, labelling claims as documented /
reported / observed / inferred, with any candidate packets for Bob to OK in a
later probe stitch. Save nothing of the vendor bundle in the repo.
