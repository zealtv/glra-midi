# lighting-modes: report

Claude (Sonnet worker), 2026-11-13, branch `lighting-modes`. Fake pad only: no
device I/O of any kind in this stitch (I didn't even run `glra-osc lights` against
the pad), no pad writes. `./test.sh` passed (320 tests, 30 of them new) before
each commit and again after merging `main` (orientation had landed there; the
merge was clean).

## What I built

- **`glra_osc/device/lighting.py`**, vendored verbatim from glra-studio commit
  `33aa281` (SPDX header kept). `glra_osc/device/README.md` and
  `THIRD_PARTY_NOTICES.md` updated; the README now records the two limits below.
- **`glra_osc/lighting.py`**, on top of it:
  - The 13-mode table (`MODES`: number, name, reads brightness, reads speed,
    takes one colour) from `glean:k16n3-lighting` and design §5.1. Each `Mode`
    carries `verified` and `unverified` text; the comment above the table says
    which parts were seen by eye on 2026-11-13 and which weren't: direction
    (never offered), the speed column, the names of 4/5 and 9/10, and the colour
    flag on mode 5.
  - `parse` / `build` / `check` / `describe` / `changes` for the 11-byte payload
    `[1, 0, mode, brightness, speed, direction, colour flag, byte 7, h, s, v]`.
    `build` lays a `profile.Lighting` over the pad's current bytes and touches
    only bytes 2, 3, 4, 6, 8–10. Values out of range, or a colour on a mode that
    takes none, raise `LightingError`.
  - `read_payload(reader)`: one `06 0a` read (allowlisted).
  - `apply(reader, identity, lighting, directory)`: read the 11 bytes, build,
    return `unchanged` without writing (not even a backup) if equal, otherwise
    one call to the vendored `write` (private backup, `06 0b`, exact readback,
    ack check, unchanged assignments and RGB table). No `06 14`, no `06 12`,
    nothing past the 11 bytes; tests assert the packet.
  - `lights_command` and `connect`: opens the pad's vendor interface, non-exclusive.
- **`glra-osc lights [--profile FILE] [--apply]`** (`glra_osc/cli.py`). Plain
  `lights` prints the pad's mode. `--apply` loads the profile's `[lighting]`
  (the user's profile unless `--profile`), prints the pad's mode, the payload
  it would write and each changed field, says every write lands in flash, asks
  `[y/N]`, then writes. "Already set" skips the prompt. Nothing else writes
  lighting: `profile.py`, `runner.py`, `engine.py`, `monitor.py` and `mapping.py`
  don't import `lighting` (a test checks the source).
- `[lighting]` parsing was already in `profile.py` from `profile-model`; I left it
  alone. A test checks that its mode range and colour-mode set agree with my table.

## Departures from the stitch text, and why

1. **The vendored write can't run on Bob's pad as shipped.** Two limits: `MODES`
   knows only 0, 1, 2, 4, and `transactions.validate_status` accepts only firmware
   100 / PID 0x246D (Bob's pad: 103 / 0x2475). Rather than edit vendored code,
   `apply` widens both for the length of one write, under a lock, and restores
   them after (a test checks the restore, including after a failed write). It adds
   exactly Bob's fingerprint, as `unique-assignments` did on 2026-11-12. That is a
   decision for Bob (L1 in `questions.md`); I took the default so the code works
   on the tour.
2. **Unused fields stay as read** (L2): `apply` changes brightness or speed only
   when the mode reads that byte. The design's list of bytes is the upper bound.
3. **Colour off keeps HSV as read** (flag 0, bytes 8–10 untouched).

## How I checked

`./test.sh` (ruff + unittest). `tests/test_lighting.py`, with a `FakePad` that
answers `06 0a`, the status and table reads the vendored write needs, and
records every packet:

- payload build and parse for every mode (all 13), with and without colour; bytes
  outside {2, 3, 4, 6, 8, 9, 10} never change; bad headers, lengths and modes refused;
- out-of-range brightness, speed, mode, colour and colour-on-a-no-colour-mode refused,
  and nothing reaches the pad;
- every mode through `apply` once: one 65-byte `06 0b` packet, backup written
  before the write, readback verified; the packet carries no `06 14` / `06 12` and
  no bytes past the 11;
- skip when the pad already holds the payload: zero writes, no backup file;
- readback mismatch: reported with "readback did not match", one write, no retry,
  an `-lighting-error.json` record left;
- firmware 104 refused with no write; firmware 100 still passes the original check;
  the vendored `MODES` and `validate_status` restored after success and failure;
- `lights` / `lights --apply`: prints, shows the diff, asks, writes on `y`, doesn't on
  `n`, no prompt when already set, errors for a missing `[lighting]` section or a
  bad profile, nonzero exit with the reason on a readback mismatch.

## Not built

- Nothing in the app (that is `app-device-panel`; it can call `lighting.apply`,
  `read_payload`, `describe` and the `MODES` table). `connect()` runs on the
  caller's thread; the design wants the app's write on a worker thread, which
  `app-device-panel` has to arrange.
- No direction control, no per-key colours, no `06 14`.
- No restore-from-backup command; the backup JSON holds the old payload
  (`before`) and a manual restore means a profile with that mode.
- The `lights` command has no `--yes`.

## Checks that need Bob at the pad (for the tour)

All with Bob watching; each lighting write persists to flash, so keep them few.

1. Answer **L1**: allow lighting writes on firmware 103 / PID 0x2475.
2. `glra-osc lights` (a read): prints the mode the pad shows now (stock: Flow (rows),
   mode 4, brightness 4, speed 3).
3. `glra-osc lights --apply` with `[lighting] mode = 2`, brightness 4, speed 2:
   the diff looks right, the prompt appears, the write reports "written and read back",
   the pad breathes, and a backup file exists under
   `~/Library/Application Support/glra-osc/backups/`. Run it again: "already set".
4. A colour: `color = [0, 255, 255]` in Breathing, then Steady, Flow, Raindrop,
   Meteor and Lit on press: the pad shows one hue (the finding says it did in
   1, 2, 4–7, 11). Mode 5 specifically (the finding groups it with 4–7).
5. The **speed column**: for each mode marked as reading speed, does speed 0 vs 4
   visibly change it? For Steady and Custom (marked as not reading it) does it change
   nothing? Correct `MODES` and the design's §5.1 table where it doesn't.
6. **Names**: which of 4/5 runs along rows or columns; which of 9/10 is "Ripples 2".
7. **Off, then on** (L3): Off, then Breathing; the animation should look as it did.
8. **Spectrum / Starry sky / Ripples with a colour**: the profile parser refuses
   `color` there; if the pad does honour it, move the mode into `LIGHTING_COLOR_MODES`
   (`profile.py`) and the table.
9. Confirm the key assignments and the 25 unique codes are intact afterwards (the
   write path checks the assignment tables and the RGB table before and after;
   `glra-osc monitor` covers the rest).

## Open questions

`questions.md` here: L1 (firmware 103 gate), L2 (unused fields stay as read), L3 (Off,
then on). Design Q6 (mode names and fields) stays open; the tour checks it.
