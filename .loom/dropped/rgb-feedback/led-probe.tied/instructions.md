# led-probe — test per-key and live lighting on the pad

**Needs Bob at the pad.** Suggested model: Opus.

Follow `../led-research*/research.md`'s probe plan. Before each *new* write
command, show Bob the exact packet and get his OK. Back up lighting state and
the RGB memory first, and restore at the end (and on error).

Answer, with evidence in `findings.md` beside this file:
- Does the pad have per-key LEDs, and which LED index is which physical key
  (use `glra_osc/device/layout.json` key numbering)? Bob looks at the pad.
- Which commands set a single key / all keys, and do they take effect live?
- **Flash or RAM:** does a per-key change survive a replug / power cycle? Does
  any "save"/"apply" step exist separately? (A change that survives a replug
  is very likely flash: limit those writes to a handful during the probe.)
- Rate and latency: how many updates per second the pad accepts with valid
  acks (only for commands believed to be RAM-only), and visible latency.
- With `glra-osc monitor` running, do lighting writes on the vendor interface
  drop or delay key/dial reports?
- Do the firmware's global animations (Breathing, Rainbow) override per-key
  colours, or coexist?
Record the outcome as a glean finding (e.g. `k16n3-lighting`).

## Updates from `led-research` (2026-11-12; see `../led-research*/research.md`)

Read research.md §2, §7 and §8 first; they hold the packets and the step order.
What changed for this stitch:
- **Custom mode is value 12 on this pad** (vendor layout file for `36ae:2475`), not 5.
  First step is a mode switch with *no* per-key write: the stored table already
  holds a red X (keys 1, 4, 6, 7, 10, 11, 13, 16), so Bob should see it.
- **Only bytes 0–83 of the `06 13` read are colour** (28 triples, indexed by slot).
  Bytes 84+ equal the keymap. Restrict probe writes to the 16 key slots
  (offsets `3 × slot`, slots 0–3, 7–10, 14–17, 21–24); reject any other offset
  and never use the bulk write (`06 12`) here. Past byte 83 a write could rewrite Bob's assignments.
- The commands to ask Bob about: `06 0b` (mode 12, then the restore to
  `0100040403030008ffffff`) and `06 14` (single key). Optional read: `06 16`.
- Treat both writes as possibly flash-backed until the persistence test
  (research.md §8 step 4) says otherwise; keep the count small, and skip the
  rate test if the colour survives a replug.
- Restore means: the global payload above, plus rewriting the red X (slots 0, 3, 8, 9, 15, 16, 21, 24)
  and zeros elsewhere in 0–27, verified by `06 13` twice. Do this on error too.
