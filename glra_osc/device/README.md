# glra_osc.device

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

Changes from upstream: none to the code. The tests import `glra_osc.device`
instead of `macropad` (`tests/test_device_*.py`, from `tests/test_safety.py`
and `tests/test_transactions.py`).

`model.py` and `learn.py` came along because `transactions.py` imports
`VISIBLE_SLOTS` from `model.py`, which imports `usage_name` from `learn.py`.
Lighting (`lighting.py`) stays out until `loom:lighting-modes` (`config-app`).

To sync with a newer glra-studio, diff against the commit above and update
this note.
