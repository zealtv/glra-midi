# unique-assignments: done 2026-11-12, with Bob at the pad

- **Firmware:** Bob's pad reports **firmware 103, internal PID 0x2475**. glra-studio only
  tested writes on 100 / 0x246D. Bob approved a one-slot trial. `program.py` allows exactly
  this fingerprint (the vendored module is unchanged), and every write still goes through
  `write_one` (backup, write, then a readback of all 6 tables, plus the ACK check).
- **Trial:** key 1 → F13 verified on readback (only slot 3 changed) and with a physical
  press. The other 24 writes were then verified the same way, with no error files.
  Records are in `transactions/`. The full table before writing is in `pre-write-backup.json`.
- **Physical check:** one press per control (`raw-report-capture.tied/captures/7-allcontrols.jsonl`)
  gave exactly one unique code each. Clockwise sends glra-studio's "ccw" slot code
  (E5 / E8 / F2), so its direction labels run backwards on this pad.
- **Layout:** `glra_osc/device/layout.json` is now final (provisional: false).
  - Keys 1–12 = F13–F24 (`0x68–0x73`); keys 13–16 = `0x46–0x49`.
  - Dials (push / ccw / cw): 1 = E3/E4/E5, 2 = E6/E7/E8, 3 = F0/F1/F2.
  - Keys are numbered from the top-left with the dials along the top edge; dials run 1–3 left to right.
- **Restore to stock:** `.venv/bin/python program.py --restore stock-backup-2026-11-12.json --apply`.
  It uses the same verified path. Run it from the repo root with this file's path.
- **Without glra-osc running:** F13–F24 do little on macOS, but Insert (key 16)
  types `ESC[2~` in a terminal, and PrintScreen/ScrollLock/Pause may do something in some apps.

## Revision, 2026-11-12 (DAW check)
Bob saw keys 2, 3, 13 and 14 (F14, F15, PrintScreen, ScrollLock) change screen brightness
during the live run, at least after a replug (see mvp-acceptance). Those keys were
reprogrammed to Home `0x4A`, PageUp `0x4B`, End `0x4D` and PageDown `0x4E`, with verified writes,
so the pad can't touch brightness even when glra-osc isn't running.
