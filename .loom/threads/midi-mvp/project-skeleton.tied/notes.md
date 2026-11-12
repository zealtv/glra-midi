# project-skeleton notes

## MIDI binding: `rtmidi2` (1.5.0)

Chose `rtmidi2>=1.5.0` over `python-rtmidi`, as the stitch suggested:

- On 2026-11-12, `rtmidi2` 1.5.0 installed from a macOS cp314 wheel into the
  Python 3.14 venv (`/opt/homebrew/bin/python3.14`) with no compiler step.
  `python-rtmidi` 1.5.8 has wheels only up to cp312 (per the stitch text, not
  re-checked), so it would have meant a second Python.
- `MidiOut.open_virtual_port(name)` exists and works.

Check run on 2026-11-12 (no HID device touched):

1. `MidiOut().open_virtual_port("glra-osc skeleton check")`.
2. A second `MidiIn` client listed it among the sources
   (`['IAC Driver Bus 1', 'glra-osc skeleton check']`), opened it, and received a
   note-on sent from the output: `[144, 60, 100]`.
3. A separate Python process also listed the port while it was open, and no
   longer listed it after `close_port()`.

Not checked: Audio MIDI Setup's own window. The CoreMIDI source list from a
separate process serves as the stand-in; Bob can glance at Audio MIDI Setup
(MIDI Studio) while a port is open if he wants the GUI confirmation.

API notes for `midi-out`: ports come from `rtmidi2.get_in_ports()` /
`get_out_ports()`; `MidiOut` has `send_noteon`, `send_noteoff`, `send_cc` and
`send_raw`; `MidiIn.callback = fn(msg, timestamp)`.

## What got vendored, and one deviation

Vendored `backend`, `descriptor`, `protocol`, `transactions`, `storage` as
listed, plus `model.py` and `learn.py`, which the instructions did not name.
`transactions.py` imports `VISIBLE_SLOTS` from `model.py`, and `model.py`
imports `usage_name` from `learn.py` (as of glra-studio `33aa281`). `learn.py`
also holds a passive capture routine that `raw-report-capture` may find
useful. Neither needs PySide6. Code is unchanged from upstream.

## Tests

The upstream tests `test_safety.py` and `test_transactions.py` came across with
only their import paths changed (`tests/test_device_*.py`): 22 tests, all pass.
They use fakes and patch `backend.enumerate_devices`, so they don't open the pad.
