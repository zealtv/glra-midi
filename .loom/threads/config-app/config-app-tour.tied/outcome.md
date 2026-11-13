# config-app-tour: outcome

Bob, 2026-11-13, after trying the app: "tested the app - working well enough for
a first release." He then asked for run instructions in the README and to move
on to `public-release`. Tied on that word by Claude (orchestrator), 2026-11-13.

Not answered as of the tie, so still open and carried to the backlog or a
later tour: L1–L3 (lighting on firmware 103), P1 / review finding 3 (renumber
layer-set keys on layer removal), P2, apply-as-you-type (review 4b), inspector
width, port change on reload, Q6 mode names, and review findings 5, 8–13. See
`tour.md` for each. Not captured: which tour steps Bob ran, or whether he made
a lighting write.

## Tour answers (Bob, 2026-11-13, later the same evening)

Bob ran the tour after the tie and reported:

- **3.3 lighting:** the modes "do seem to be setting correctly", but after the
  first change each Apply reported a readback mismatch (Flow (columns); then
  Breathing with a colour, Custom, Lit on press). Two screenshots. →
  `loom:fix-lighting-readback`. L1 not answered in words; Bob made the writes.
- **Quitting the app** shows "Python quit unexpectedly". → `loom:fix-quit-crash`.
- **P1:** yes (renumber layer-set keys) → `loom:layer-removal-renumber`.
- **P2:** yes (lighting defaults brightness 4, speed 2). **L2:** yes.
- **Port on reload:** good. **Apply as you type:** good. **Inspector width**
  for CC momentary: fine.
- "re left for me" and "re 6 left for me": Claude's reading, the §6 "Left for
  you" items and the Q6 mode-name check stay with Bob; both get fixed or
  checked after the release.
- "release first, fix later", as a patch bump → thread `patch-0.1.1`.

Not captured: §4 orientation, §3.4–3.5, Q1–Q3/Q7 readings.
