# mvp-acceptance — end-to-end check with Bob, then tie the goal

**Needs Bob at the pad.** Suggested model: Sonnet.

Run `glra-osc run` with the default mapping and walk this checklist with Bob,
recording results in this stitch:
- [ ] Port appears in Bob's DAW (and Audio MIDI Setup / MIDI Monitor).
- [ ] All 16 keys send their notes; toggle mode works on at least one key.
- [ ] Each encoder: CW/CCW relative CC is accepted by the DAW's MIDI-learn;
      absolute mode moves 0–127 and clamps.
- [ ] Each encoder push works.
- [ ] Pad types nothing into apps; other keyboards fine.
- [ ] Unplug/replug mid-run recovers, with no stuck notes.
- [ ] Ctrl-C leaves nothing behind (no suppression state left, no stuck notes).
- [ ] README has install + run + mapping instructions.

Then tie `midi-mvp` and ask Bob which sketch goal to flesh out next.
