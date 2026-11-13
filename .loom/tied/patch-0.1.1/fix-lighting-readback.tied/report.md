# fix-lighting-readback — report

Worker: Claude Sonnet 5.5, 2026-11-13, branch `fix-lighting-readback`.

## Built

- `glra_midi/lighting.py`: `readback_differences(expected, after)` compares mode,
  brightness and speed (only where the mode reads them), direction, the colour
  flag, and HSV only when the sent flag is on. It ignores byte 7 and HSV with the
  flag off, and reports any other difference by the same field names as `changes`.
- The vendored `device/lighting.py` stays unedited. It still does an exact
  compare, so `apply` patches `device.lighting.read` for the length of one write
  (`_tolerant_readback`, inside the existing gate's lock). After the write has gone
  out, a read that differs from the sent bytes only in ignored fields reaches the
  vendored check as the sent bytes. Its other checks (ack, assignments, RGB data) still
  run. The patch is undone in a `finally`; a test covers that.
- When the pad held normalised bytes, `apply`'s result has `after` = what the pad
  really holds (so the app's "Pad now" shows the truth), `normalised` (byte, sent,
  held), and one extra record file `…-lighting-normalised.json` beside the backup.
  The vendored `…-lighting-result.json` is saved while the check sees the sent
  bytes, so its `after` says "sent"; the new file and the audit log carry the real bytes.
- The ack check gets the same tolerance (`_SentDevice.read`), in case the pad
  echoes stored rather than sent bytes. **Unverified**: the two captures fail
  at the readback, before the ack check ran.
- Fixtures: `tests/fixtures/lighting_readback_captures.json`, both captures. The
  stitch gave only the byte tails, so I took the full 11 bytes from the two
  screenshots in `evidence/`.
- Tests (`tests/test_lighting.py`, `ReadbackTests` and new `ApplyTests`): both captures
  count as read back, each other field still reports, both captures apply as
  "verified", a real difference beside a normalised byte still raises
  `WriteNotConfirmed`, and the vendored `read` is restored.
- `glean:k16n3-lighting` revised with byte 7 and the h/s/v normalisation (index rerun).
  `CHANGELOG.md` has a Fixed line under Unreleased. Docstring in `app/device.py` updated.

## Not done

- **Check at the pad (with Bob)**: not possible in this run, and nothing was
  written to a pad. To check: Flow (columns) one colour off, Breathing with
  colour, Custom, Lit on press, in that order, each should end "Applied and read
  back." Also watch whether the ack check passes (see above).
- Review finding 2 (per-mode HSV not kept with the flag off) is answered only
  in that the check no longer cares; I did not look at the review text itself.
- I did not touch the loom, the queue or other stitches.

## Checked

- `./test.sh` (ruff + 602 unittest) passes. All on fakes; no pad, no
  `lights --apply`, no app against a real pad.

## Open questions

None needed Bob's decision (no `questions.md`). Two guesses: brightness/speed are
compared only where the mode reads them, as the stitch says; direction is always
compared, since no capture shows firmware rewriting it.
