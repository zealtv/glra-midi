# first-release — glra-midi 0.1.0 on GitHub (with Bob)

Each outward step waits on Bob's word at the time.

1. Bob's decisions on `publication-audit` applied.
2. Bump to 0.1.0, date the changelog entry, `tools/release-check.sh 0.1.0`.
3. Push main, tag `v0.1.0`, push the tag.
4. Make the repo public (`gh repo edit --visibility public`), add a
   description and topics.
5. GitHub release `v0.1.0` with the changelog notes, wheel and sdist.
6. Open and pin the `chip-info` issue from `call-for-chip-info`.
7. Message Bob the release link; record the release in lore.

## Done (Claude, with Bob, 2026-11-13)

All seven steps, each outward one on Bob's word in the session:
`release: 0.1.0` (`d474fbc`) passed `tools/release-check.sh 0.1.0`; main and
`v0.1.0` pushed; repo public with description and topics; release
https://github.com/zealtv/glra-midi/releases/tag/v0.1.0 with wheel and sdist
(the first `gh release create` got HTTP 404 right after the visibility change,
a retry worked); `chip-info` label made and issue #1 opened and pinned. Record:
`lore:2026-11-13-first-release-0-1-0`.
