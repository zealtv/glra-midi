# MVP acceptance, 2026-11-12, with Bob at the pad

- Silence check (`silence-check.sh`, no replug): all 25 controls gave no keystroke
  leaks and no volume/mute change, and the MIDI was exact (notes 36–51, relative CC 16–18,
  pushes 52–54). The runner restored the mapping on exit.
- DAW (Bob): notes, toggle and dials all worked. Keys 2, 3, 13 and 14 (F14/F15/PrintScreen/
  ScrollLock) changed brightness, so they were reprogrammed to Home/PgUp/End/PgDn.
  Replug race: macOS overwrote our mapping after the replug, so the pad leaked and
  exit wiped Bob's CapsLock entry. Fixed in `bac9739` (re-check every 2 s; restore removes only ours).
- Final check (`checks/final-session.log`, `checks/final-midi-in.log`): MIDI from keys
  2/3/13/14/16 arrived before and after the replug, with toggle working. Exit restored Bob's
  CapsLock entry (2 entries). **One leak:** `ESC[1~` (Home, key 2) typed once
  just after the replug, inside the up-to-2 s window before the re-check reapplied.
  Bob didn't report brightness changes this time. → follow-up `replug-leak-window`.
- Not covered: the absolute-dial (enc 3) clamp, explicitly (Bob reported "that works"
  for the DAW run overall), and a README walkthrough.
