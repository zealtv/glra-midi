# glra_midi.device

Vendored from [glra-studio](https://github.com/imolitor/glra-studio)
(`macropad/`, GPL-3.0-only), source commit `33aa281`
("License GLRA Studio under GPL-3.0-only"). SPDX and copyright headers are
kept as they were.

| Here | From | Role |
|---|---|---|
| `backend.py` | `macropad/backend.py` | enumerate/select/open; VID/PID allowlist; forces non-exclusive opens |
| `descriptor.py` | `macropad/descriptor.py` | HID report descriptor parser |
| `protocol.py` | `macropad/protocol.py` | `Reader`, allowlisted vendor reads |
| `transactions.py` | `macropad/transactions.py` | one assignment write with backup and readback |
| `storage.py` | `macropad/storage.py` | backup files |
| `model.py` | `macropad/model.py` | slot layout, `VISIBLE_SLOTS`, labels (needed by `transactions.py`) |
| `learn.py` | `macropad/learn.py` | `usage_name` (needed by `model.py`); passive key capture |
| `lighting.py` | `macropad/lighting.py` | lighting payload checks and the one guarded write (backup, write, exact readback) |

Changes from upstream: none to the code (checked again for `lighting.py`, 2026-11-13). The tests import `glra_midi.device`
instead of `macropad` (`tests/test_device_*.py`, from `tests/test_safety.py`
and `tests/test_transactions.py`).

`model.py` and `learn.py` came along because `transactions.py` imports
`VISIBLE_SLOTS` from `model.py`, which imports `usage_name` from `learn.py`.
`lighting.py` came in with `loom:lighting-modes` (`config-app`, 2026-11-13), from
the same source commit. Two limits in it matter here, and `glra_midi/lighting.py`
works around both without editing this file:

- `MODES` names only 0, 1, 2 and 4 (tested on firmware 100); `validate` refuses
  the rest. The wrapper widens `MODES` to firmware 103's 0-12 for the length of
  one write.
- `write` calls `transactions.snapshot`, whose `validate_status` accepts only
  firmware 100 / PID 0x246D. The wrapper lets exactly Bob's fingerprint
  (firmware 103, PID 0x2475) through for the length of one write, as
  `unique-assignments` did on 2026-11-12 (`.loom/tied/midi-mvp/unique-assignments.tied/`).

To sync with a newer glra-studio, diff against the commit above and update
this note.
