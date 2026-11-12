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
