# fix-app-apply-and-quit: report

Claude (Sonnet 5.5 worker), 2026-11-13. Built to `config-app-review` findings 2, 4a and 6
(`config-app-review.tied/review.md`). No device I/O; every test and capture runs on fakes.
`./test.sh` passes after merging main (ruff clean, 577 tests OK).

## What I built

**Finding 2: honest result when the write went out but wasn't confirmed.**
- `glra_osc/lighting.py`: new `WriteNotConfirmed(RuntimeError)` with `before`, `expected`, `after`
  (hex; `after` is None when the pad couldn't be read again), `backup` and `detail`.
  `lighting.apply` raises it when the vendored `write` raised *after* `device.write` returned
  (it watches that with a thin reader wrapper, `_SentFlag`, so vendored code stays untouched).
  It re-reads the pad (the allowlisted `06 0a` read) to fill `after`, takes the backup path from
  the vendored error text, and drops the vendored "Further writes are paused." sentence.
  Any other error (firmware gate, "Lighting changed outside the app", a failing `device.write`)
  still propagates as before and means nothing was sent.
- App: `Controller._pad_done` shows `WriteNotConfirmed` as a warning-coloured line ("Written to
  the pad, but it did not read back as expected. Before …, expected …, after …. Backup: …"),
  updates "Pad now" from the `after` bytes, and keeps Apply enabled (nothing pauses writes).
  "Not applied: …" remains only for errors where nothing was sent. `DevicePanel.qml` colours the
  new `warn` kind.
- `glra-osc lights --apply` prints the same text (it already printed the exception).
- Vendored tolerance untouched (`glra_osc/device/` not edited).

**Finding 4a: note hint.** `inspector.describe` blanks `noteName` when `drafts["note"]` carries an
error (other fields' errors leave it alone).

**Finding 6: quit mid-write.** `Controller.applying` (property) is true while Apply runs.
`requestQuit` then waits: it shows the notice "Waiting for the pad write to finish before
closing." and, when the write ends (success or failure), carries on to the usual unsaved-changes
check and quits. `Main.qml`'s `onClosing` refuses while `applying` (as it does while dirty).
`gui.main` calls `controller.shutdown()` (joins `PadWorker`) after `app.exec()`.
I chose "wait with a message" over a plain refusal so the quit Bob asked for still happens.

## Checked

- Tests: `tests/test_lighting.py` (mismatch with before/expected/after/backup; no "not applied"
  or "paused" in the text; a bad ack after a correct payload; an unreadable pad after the write;
  firmware refusal and a failing `device.write` stay plain errors), `tests/test_app_device.py`
  (warning shown with all four values, "Not applied" kept for nothing-sent, quit waits for a
  success and for a failure, immediate quit when idle, `shutdown` joins a running call),
  `tests/test_app_qml.py` (a real window refuses `close()` during an Apply, then closes when it
  ends), inspector model and controller tests for the hint.
- Captures in `captures/`: `inspector-invalid.png` (note 300: hint blank; the old capture showed
  "C1") and `device-panel-apply-mismatch.png` (the new capture state
  `device-panel-apply-mismatch`).

## Not done / notes

- A `device.write` that itself raises (an I/O error mid-send) stays "Not applied: …" with the
  vendored backup line, though the pad may in theory have received it. I treat "sent" as
  `device.write` returned, and can't tell more without a real pad.
- Cmd-Q on macOS goes through the same `closing` handler, so it should wait too; I only tested
  `close()` offscreen.
- Reads (Read pad) aren't treated as blocking a quit; `shutdown` joins them.
- No capture of the "waiting to close" banner (it needs a stalled write).
- Tour list: with the mismatch message now visible, the tour's check "set Breathing with no
  colour, then Flow (columns) with no colour" (review finding 2) still applies.

## Open questions

None for Bob; no `questions.md`.
