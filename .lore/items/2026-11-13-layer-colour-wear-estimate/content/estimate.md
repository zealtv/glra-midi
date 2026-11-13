# Changing the pad's colour on layer changes: wear and lifetime (estimate)

Claude (Opus orchestrator), 2026-11-13 ~15:20 AEDT, answering Bob: "can you
give me an assessment of how feasable it would be to switch colour state on
bank changes? what sort of estimate ranges could you give me for lifetime use
given say 10 to 50 bank changes a session. 10, 50, 300 sessions a year ...
it does feel as though being able to set colour per layer could be very
useful." Bob's response: "just add these estimates to the lore. we'll won't
implement yet". Desk estimate from `glean:k16n3-lighting` only; no new
measurement or research. Endurance figures are assumptions, not this chip's specs.

## Short answer

It's feasible for light to moderate use if each layer gets one colour for the
whole pad. Heavy daily use is risky, and per-key colours per layer would wear
the flash too fast. One unknown drives every number below: how many writes the
pad's flash survives. Nobody has measured it, and the chip isn't identified.

## What was known (2026-11-13 probe)

- No temporary setting: every lighting write gets saved to the pad's flash.
  No RAM-only path and no lazy commit was found.
- Pad-wide colour costs one write: a factory mode with one fixed hue (e.g.
  Steady + HSV) is a single `06 0b`. One colour per layer means one write per
  layer change.
- Per-key colours cost up to 16 writes: Custom (mode 12) takes one `06 14` per key.
- Not measured: flash endurance, and whether the firmware spreads writes
  (wear levelling) or rewrites the same page each time.

## Estimates

Layer changes per year = changes per session x sessions per year:

| Use | 10 changes/session | 50 changes/session |
|---|---|---|
| Light (10 sessions/yr) | 100/yr | 500/yr |
| Moderate (50 sessions/yr) | 500/yr | 2,500/yr |
| Daily (300 sessions/yr) | 3,000/yr | 15,000/yr |

Assumed endurance: 10k writes (cheap MCU flash, no wear levelling) to 100k
(a common rating). Wear levelling, if the firmware does it, would multiply these.

One colour per layer (one write per change), years until the budget runs out:

| | 100/yr | 500/yr | 2,500/yr | 3,000/yr | 15,000/yr |
|---|---|---|---|---|---|
| 10k writes | 100 | 20 | 4 | 3.3 | 0.7 |
| 100k writes | 1,000 | 200 | 40 | 33 | 6.7 |

Per-key colours per layer (16 writes per change): light use about 6 to 60
years; moderate use (2,500 changes/yr) about 3 months to 2.5 years; daily
heavy use (15,000/yr) about 2 weeks to 5 months.

## The risk beyond worn LEDs

Bytes 84 onward of the `06 13` lighting block mirror the key assignments,
which suggests lighting and keymap share a flash region. If so, wear might
corrupt the stored key codes too. glra-studio can rewrite assignments, so that
should be recoverable (not verified).

## Ways to make it safer

1. One colour per layer only: one write per change, never per-key colours.
2. Write once the layer settles: wait about 300-500 ms after the last change,
   so scrolling through four layers costs one write.
3. Skip writes when nothing changes (e.g. two layers sharing a colour).
4. Keep a write budget on the host: count writes in a host-side file, show
   it, stop writing past a cap.
5. Measure the real endurance: write to a second, sacrificial pad until it
   fails; confirming the chip lead (M9F9520) and its datasheet would narrow
   the range too.

With 1-3, light and moderate use looked comfortable and daily heavy use worth
avoiding. Custom firmware (`loom:custom-firmware`) remains the clean route to
freely changing colour.
