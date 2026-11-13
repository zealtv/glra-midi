# lighting-modes: questions for Bob

Raised by Claude (Sonnet worker on `lighting-modes`), 2026-11-13. Each has its
default taken; all are cheap to change. `config-app-tour` can put them in front
of Bob next to the design's Q1–Q9 and `profile-model`'s P1–P2.

**L1. Lighting writes on firmware 103 (needs Bob's yes before the first real write).**
glra-studio's vendored `transactions.validate_status` accepts only firmware 100 /
internal PID 0x246D; Bob's pad reports firmware 103 / 0x2475
(`glean:k16n3-hid-interfaces`). Without a change, the vendored `lighting.write`
would refuse Bob's pad at its first `snapshot`. *Default taken:*
`glra_osc/lighting.py` lets exactly the fingerprint `(1, 0x2475, 103, 6, 1)`
through for the length of one `apply`, the way `unique-assignments` did for
assignment writes on 2026-11-12 (Bob approved a one-slot trial then). The
vendored files stay unchanged; any other firmware still hits the original check.
Bob approved that for assignments, not for lighting; the tour is where he says yes
or no. Alternative: keep the gate shut and make Bob's pad write through a separate
approved path.

**L2. What `apply` does with a field the mode doesn't read.** Design §5.3 says
change bytes 2, 3, 4, 6 and 8–10. *Default:* brightness (byte 3) and speed
(byte 4) change only when the mode reads them (table in `glra_osc/lighting.py`);
otherwise the pad's byte stays as read. The colour flag follows the profile
(colour present = 1, absent = 0). HSV changes only when a colour is given;
otherwise it stays as read. *Why:* fewer writes of values the probe never
tied to that mode, and "already set" matches more often. The speed column is
itself inferred (Q6).

**L3. Off, then on again.** glra-studio writes Off as `01 00` plus nine zero
bytes, and its `DEFAULT` (`0100040403030008ffffff`) restores usable direction and
byte 7 when switching on from that. This stitch keeps direction (byte 5) and
byte 7 as read, so a pad left in glra-studio's zeroed Off would come back with
direction 0 and byte 7 = 0, not 3 and 8. We never write a zeroed Off ourselves
(mode 0 changes only byte 2, and the flag), but a pad last touched by glra-studio
could hold one. *Default:* follow the design (keep as read). To check at the tour:
set Off, then Breathing, and see that the animation looks as it did.
