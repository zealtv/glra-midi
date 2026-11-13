# led-commit-timing findings (Bob's K16_N3, fw 103, 2026-11-13)

Script: `../led-modes.tied/probe.py`; baseline `../led-probe.tied/baseline.json`.

- 12:50:40: from stock mode 4 sent `06 0b 0b 00 00 01 00 01 04 03 03 00 08 ff ff ff`
  (mode 1, Steady). Ack 1.65 ms; `06 0a` read back mode 1. Bob unplugged as
  soon as the pad changed (he'd been told to unplug at the change, after a
  10 s countdown; reaction time likely well under a second), then replugged.
- **Bob saw the static gradient (Steady) after the replug.** `06 0a` =
  `0100010403030008ffffff`. (observed)
- So `06 0b` also commits to non-volatile storage within a human reaction time
  of the write, despite its ~1.6 ms ack: no lazy save on a timer of a second or
  more. A save deferred by a few hundred ms can't be ruled out by hand. (observed / inferred)
- Implication: the vendor UI's undebounced colour-wheel streaming writes flash
  per event, and host-driven global colour/brightness modulation would wear
  flash just like per-key writes. (inferred)
- Restored: `06 0b … 04 …` (ack 1.58 ms); `06 0a` and `06 13` equal the
  baseline, two reads each. (observed)
