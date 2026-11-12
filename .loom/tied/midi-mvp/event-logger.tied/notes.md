# event-logger notes (2026-11-12)

## Built
- `glra_osc/events.py`: `ControlEvent(control, action, t)` and `format_event`
  (`[12:01:03.122] KEY 07 DOWN`).
- `glra_osc/decode.py`: pure `Decoder.feed(source, bytes, t) -> [ControlEvent]`,
  with `source` = `"keys"` (interface 0) or `"consumer"` (interface 1). It keeps
  only the held-key set and any held dial push. `load_layout()` reads
  `glra_osc/device/layout.json`.
- `glra_osc/device/layout.json`: **provisional**: Bob's key numbering (usage ->
  `key.N`) and the three stock dial codes.
- `glra_osc/monitor.py` (new file, so `cli.py` stays small): reader thread per
  interface, one queue, main thread decodes and prints. `glra-osc monitor [--raw]`.
- `pyproject.toml`: one added line so `layout.json` ships as package data
  (mapping-config added the `[tool.setuptools.package-data]` table for `*.toml`).
- Tests: `tests/test_decode.py`, fixtures `tests/fixtures/captured_reports.jsonl`
  (the `hid` records of captures 1 and 3, trimmed to source/hex/t/step).

## Decisions
- **Dial turn = one event at the press report** (`enc.? cw|ccw`); the `03 00 00`
  that follows 1-2 ms later gives no event. **Dial push = `down` at press, `up`
  at the real release.** If a turn usage arrives while a push is held (seen once
  in the capture), the decoder emits push `up` first, then the turn.
- **Dials decode as `enc.?`** and `enc.?.push`. The provisional layout cannot tell
  them apart; `unique-assignments` supplies `enc.1..3`. `format_event` already
  prints `enc.2.push` as `ENC 2 PUSH`.
- **Cw/ccw follow glra-studio's labels** (0xE9 = cw, 0xEA = ccw). Bob's
  capture saw "turn right" produce 0xEA, so physical direction may read
  reversed; the raw-report-capture findings leave this to `unique-assignments`.
- **Key 7 = usage 0x5B is inferred**, not observed (no report in either capture
  pass). It is the only unseen keypad usage, and `keys_inferred` in the layout says so.
- Unknown usages decode to `key.unknown:0x04` / `consumer.unknown:0x00cd`
  rather than being dropped; an unknown consumer usage gets a `down` and no `up`.
- A boot-protocol rollover report (`01` fill) is ignored and the held set kept.
- Source is chosen by HID interface number (0 keys, 1 consumer); interface 2 (vendor)
  is never opened. Opens go through the vendored `open_device`, which forces
  non-exclusive and checks VID/PID. Nothing is written to the pad.
- Unplug: the interface's thread ends on a read/open error, `monitor` prints
  `# <source> interface lost`, resets the decoder, and rescans once a second.
- `--raw` prints a `RAW <source> <hex>` line before each report's events.
- Fixture note: Bob's capture steps ran fast, so a release can land in the next step's
  label, and the capture ends with key 1 still held. The tests account for both.

## Verified
- `./test.sh` passes (80 tests, 19 of them new).
- Read-only smoke test, 4 s with no input: `monitor --raw` opened the keys and
  consumer interfaces and exited 0 on SIGINT.

## For Bob's hardware check
1. `glra-osc monitor --raw` at the pad: press each key, check the `KEY nn` numbers
   against your numbering. **Press key 7 first** (dead switch, or does 0x5B show up?).
2. Turn and push a dial: confirm `ENC ? CW/CCW` and `PUSH DOWN/UP`, and which
   physical direction reads as CW.
3. Unplug and replug the pad while `monitor` runs: expect "interface lost" then
   "interface open" lines and no crash. **Untested here.**
4. Ctrl-C closes cleanly (checked once with SIGINT, no input).
