# glra-midi 0.1.0, the first public release (2026-11-13)

Claude cut and published glra-midi 0.1.0 with Bob present: tag `v0.1.0` on commit `d474fbc`, the repo made public with full history, a GitHub release carrying the wheel and sdist, and the pinned `chip-info` issue #1.

## Source

Claude, `first-release` stitch, 2026-11-13, each outward step on Bob's word in the session:

- `tools/release-check.sh 0.1.0` passed on main (tests, version and changelog, build from
  `git archive HEAD`, contents, fresh install printing `glra-midi 0.1.0`).
- Pushed main (`fd102f5..d474fbc`, a fast-forward of 122 commits) and tag `v0.1.0`.
- `zealtv/glra-midi` made public; description "Host-side middleware that turns the G-LRA
  K16_N3 macropad into a silent MIDI controller (macOS)"; topics midi, macropad, coremidi,
  macos, hid, midi-controller, python, pyside6.
- Release: https://github.com/zealtv/glra-midi/releases/tag/v0.1.0 (the first
  `gh release create` returned HTTP 404 just after the visibility change; a retry worked).
- Issue: https://github.com/zealtv/glra-midi/issues/1, label `chip-info`, pinned.

`content/release-notes.md` holds the notes as published (the changelog's 0.1.0 section);
`content/sha256.txt` the attached files' checksums.

## Where it went

`loom:first-release` (tied with this record); `path:CHANGELOG.md`; `path:README.md` Status line.
