# glra-osc

Host-side middleware that turns the G-LRA K16_N3 macropad into a silent MIDI
controller (OSC later). It builds on [glra-studio](https://github.com/imolitor/glra-studio)
for device I/O.

**Status:** pre-alpha skeleton. As of 2026-11-12 there is no MIDI output yet;
`glra-osc --version` is the only command. Work is planned on the loom
(`.loom/`, goal `midi-mvp`).

## Setup and tests

Needs Python 3.13+ on macOS (Homebrew's `python3.14` works).

```sh
/opt/homebrew/bin/python3.14 -m venv .venv
.venv/bin/pip install -e '.[dev]'
./test.sh          # ruff + unittest
.venv/bin/glra-osc --version
```

## Licence

GPL-3.0-only, because it reuses glra-studio code. See `LICENSE` and
`THIRD_PARTY_NOTICES.md`.
