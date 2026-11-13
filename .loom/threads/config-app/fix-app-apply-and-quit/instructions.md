# fix-app-apply-and-quit — honest Apply results, the note hint, no quit mid-write

Suggested model: Sonnet. Fix stitch from `config-app-review` findings 2, 4a
and 6 (`.loom/threads/config-app/config-app-review.tied/review.md`), shaped by the orchestrator on 2026-11-13; fix before the tour.
Never write to the pad; tests use fakes.

1. **Finding 2.** When the vendored write raises after the `06 0b` went out
   (readback mismatch), the app and `lights` must say it was written but read
   back differently (before / expected / after, backup path), not "Not
   applied", and not claim later writes are paused. "Not applied" only when
   nothing was sent. Don't change the vendored tolerance.
2. **Finding 4a.** Blank the note-name hint when the Note field's draft
   carries an error (`inspector.py` noteName).
3. **Finding 6.** Refuse to close the window (or wait, with a message) while
   an Apply is running, and call `PadWorker.shutdown` after `app.exec()`.

Tests for each; recapture `inspector-invalid` and an Apply-mismatch state.
