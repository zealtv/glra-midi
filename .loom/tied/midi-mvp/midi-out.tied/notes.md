# midi-out notes (2026-11-12)

## Built
- `glra_osc/engine.py`: pure `Engine(mapping)`. `handle(ControlEvent) -> [bytes]`,
  `release_all() -> [bytes]`, `held` (names). `describe(msg)` formats a message for `--dry-run`.
- `glra_osc/runner.py`: `glra-osc run [--config FILE] [--dry-run]`. `MidiPort` is the thin
  rtmidi2 adapter (`open_virtual_port(mapping.port)`, `send_raw`); `DryRunPort` prints
  `MIDI 90 24 7f  ch 1  note on  36  vel 127`.
- `glra_osc/monitor.py`: the reader/rescan loop moved out of `run()` into `watch(decoder,
  on_report, say, on_lost)`; `monitor` and `run` now share it. `monitor` behaviour is unchanged.
- `glra_osc/cli.py`: the `run` subcommand; a `MappingError` prints `glra-osc: <msg>` and exits 2.
- Tests: `tests/test_engine.py`, `tests/test_runner.py` (runner tests stub `watch`; dry-run port).
  `./test.sh` passes, 103 tests.

## Decisions
- Momentary note/CC: `down` sends on, `up` sends off. Toggle: each `down` flips, `up` is ignored.
- Relative turn, one detent per event: twos-complement cw 1 / ccw 127; binary-offset 65 / 63;
  signed-bit 1 / 65. Absolute: value += or -= `step`, clamped 0..127, and **nothing is sent
  when the clamp leaves the value unchanged**.
- **Release on exit/disconnect**: Note Off for every held or toggled-on note, and the `off`
  value for held *momentary* CCs (a stuck CC 127 looked as bad as a stuck note). Toggled CCs
  keep their last value. The engine forgets its held state at release, so a late physical
  `up` sends nothing a second time.
- Exit paths: Ctrl-C and SIGTERM (handler raises KeyboardInterrupt, `finally` releases and
  closes the port), pad disconnect (`on_lost`), and any exception from the loop. SIGKILL
  cannot be caught; CoreMIDI drops the virtual port then, but a DAW may keep notes sounding.
- **Config reload not implemented** (optional); restart `run` to pick up a changed mapping.
- `enc.?` / `enc.?.push` events (provisional layout) produce no MIDI; `run` says so at startup.
  Dials start working when `unique-assignments` gives `enc.1..3` (no change needed here).
- Startup warning (stderr): the pad still types into apps until `silent-capture` lands.
  Status lines (`# ...`) go to stdout like `monitor`'s.
- `--dry-run` still reads the pad (read-only) and opens no MIDI port.
- Unknown-key events, wrong actions and unmapped controls are dropped silently.

## Verified (2026-11-12, no hardware button presses)
- Virtual port: a second `rtmidi2` process saw `GLRA K16` in `get_in_ports()` while `run` was
  up, and it vanished after SIGTERM (exit clean, within a second).
- `MidiPort.send` loopback: note on, CC, note off arrived byte-exact at a `MidiIn` client.
- Read-only smoke test, ~4 s, no input: keys and consumer interfaces opened, SIGTERM exit clean.
- `run --config /nonexistent` → `glra-osc: /nonexistent: cannot read mapping file...`, exit 2.
- Not exercised: real key/dial events through `run`, pad unplug while running.

## For Bob's hardware check
1. `glra-osc run --dry-run`, press keys: expect `MIDI 90 ..` on press, `MIDI 80 ..` on release
   (key numbering is still the provisional layout's).
2. `glra-osc run`, then in a DAW or MIDI monitor pick the source `GLRA K16`; keys play notes
   36-51 on channel 1. Expect the pad to still type numpad characters (no suppression yet).
3. Hold a key, then Ctrl-C (and separately `kill -TERM`, and unplug): expect a Note Off.
4. Dials send nothing until `unique-assignments`. Then check twos-complement CC 16-18 in
   your DAW (see mapping-config notes).
