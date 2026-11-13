# tend-nest report (worker, 2026-11-13)

## Built
The nest held one arrival, `further-chip-findings.txt`. Tended per `.nest/tend.md`:
- **Lore:** `lore:2026-11-13-further-chip-findings-m9f9520` keeps the report whole.
  The only edit: `utm_source=chatgpt.com` stripped from its links (Bob's instruction).
  `item.md` records provenance and notes that we did not reproduce its claims.
- **Glean:** `k16n3-firmware-replacement` gained a dated paragraph: the Masses Chip 2025
  catalogue row (32 KB flash, 2 KB RAM nominal vs ZXW's 2216 bytes, 44 I/O, 15-level
  stack, 3 timers, 8 PWM, USB 2.0, 48 pins), no datasheet found anywhere checked, the
  warning not to borrow M9F951's pinout, and the unconfirmed chip identity. Marked as one
  search's findings. Two triggers added; INDEX regenerated.
- **Parked notes:** `.loom/threads/custom-firmware.waiting/firmware-approaches/instructions.md`
  chip-lead section extended likewise, with the contact route and the open question.
- **Receipt:** `.nest/out/further-chip-findings-receipt.md` names the three routes.
  `.nest/in/` is now empty.

## Not done
- No stitch created (the stitch said fold into glean and notes; custom-firmware stays parked).
- Masses Chip not contacted; the drafted enquiry sits in the lore item for Bob.
- I did not open the catalogue PDF or linked pages, so the row's figures stand as the
  report states them. The 2 KB vs 2216-byte RAM difference stays unresolved.

## Checked
`./test.sh` passes (404 tests, 4 skipped) before and after; `git merge main` found
nothing to merge. `grep utm` over the kept report finds nothing. No device I/O, no
loom state touched.

## Slip
`lore.sh keep` prefixes the date itself; my first slug included it, giving a doubled
prefix. I renamed the uncommitted item directory and re-ran `lore.sh index` before
committing. Worth remembering: pass slugs without a date.

## Open questions
None blocking. For Bob: whether to send the Masses Chip enquiry.
