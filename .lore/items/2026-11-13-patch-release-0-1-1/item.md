# glra-midi 0.1.1, the tour-fixes patch release (2026-11-13)

Claude cut and published glra-midi 0.1.1 on Bob's standing word ("once 4 is complete you can publish the new release"): tag `v0.1.1` on `4b32fbf`, a GitHub release with wheel and sdist, carrying the four `patch-0.1.1` stitches.

## Source

Claude (Opus manager) with Sonnet workers in tmux panes, 2026-11-13 evening, paused once at
93% of the 5-hour window and resumed after the 21:10 AEDT reset.

- Stitches: fix-lighting-readback, layer-removal-renumber, fix-quit-crash, app-review-polish.
- `tools/release-check.sh 0.1.1` passed (621 tests, build, contents, fresh install).
- Release: https://github.com/zealtv/glra-midi/releases/tag/v0.1.1
- Shipped as a patch although review 11 makes the parser refuse `[key."01"]` and
  `version = 1.0`, which loaded in 0.1.0 (`docs/releasing.md` puts profile breaks in a minor
  bump); the profile format's `version` stayed 1. Claude's call, flagged to Bob.
- Still to check at the pad with Bob: the lighting Apply sequence reads back clean; quitting
  the app with the pad attached leaves no new `Python-*.ips`.

`content/release-notes.md` holds the notes as published; `content/sha256.txt` the checksums.

## Where it went

`loom:patch-0.1.1` (tied); `path:CHANGELOG.md`.
