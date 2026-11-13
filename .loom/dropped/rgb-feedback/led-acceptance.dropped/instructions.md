# led-acceptance — check the lighting goal with Bob

**Needs Bob at the pad.**

With `glra-osc run` playing MIDI into a DAW:
- each of the 16 keys can be set to its own colour, and Bob confirms the mapping;
- one per-key animation and one whole-pad animation run as designed;
- keys and dials still send correct MIDI while lights animate (no dropped reports);
- exit (and `lights restore`) puts back Bob's own lighting;
- no flash-wear risk is left in the default path (per `led-route`).
Record results in `results.md`; queue follow-ups as stitches.
