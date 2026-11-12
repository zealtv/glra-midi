# project-skeleton — Python package, tooling, reused HID code

Suggested model: Sonnet (well-specified).

Set up the repo as a small Python project, matching glra-studio's
toolchain so its code drops in:

- As of 2026-11-12, the only Python on Bob's Mac is Homebrew's
  `/opt/homebrew/bin/python3.14` (glra-studio's venv uses it as well).
- `pyproject.toml`: package `glra_osc`, Python >= 3.13, console script
  `glra-osc`, deps `hidapi==0.15.0` (same pin as glra-studio) and
  a CoreMIDI binding with a virtual-port API. As of 2026-11-12 on PyPI,
  `python-rtmidi` 1.5.8 (2023) only has wheels up to cp312, while
  `rtmidi2` 1.5.0 (2026-10) has macOS cp313/cp314 wheels and
  `open_virtual_port`. Prefer `rtmidi2` on 3.13+; otherwise use Python 3.12
  with python-rtmidi. Check that a virtual port shows up in Audio MIDI Setup before
  committing to one. No PySide6.
- `.venv` in the repo (gitignored), `ruff` + `unittest` like glra-studio, and a
  `./test.sh` (or similar) that runs lint + tests.
- **License:** GPL-3.0-only, because we reuse glra-studio code (GPL-3.0-only). Add
  `LICENSE`, plus a `THIRD_PARTY_NOTICES.md` crediting glra-studio
  (https://github.com/imolitor/glra-studio). Bob plans to release this
  publicly later, as with BopOS, so get attribution right from day one. Check
  with Bob if GPL looks like a problem.
- Vendor only what we need from `../glra-studio/macropad/`, keeping SPDX
  headers: `backend.py` (enumerate/select/open; it forces non-exclusive
  opens and the VID/PID allowlist), `descriptor.py`, `protocol.py` (Reader,
  allowlisted reads), `transactions.py` + `storage.py` (safe assignment
  writes with backup and readback). Lighting waits for `rgb-feedback`. Put
  them under `glra_osc/device/` and note the source commit
  (`33aa281`) in a short `glra_osc/device/README.md`. Port their relevant tests.
- `README.md` stub: what this is, status, how to run tests.
- Add the run/test commands to `AGENTS.md` once they exist.
- `.gitignore`: `.venv/`, `__pycache__/`, `.DS_Store`, private dumps/logs.

Done when `pip install -e .` and the test script both pass from a fresh clone.
