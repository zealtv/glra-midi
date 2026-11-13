# cc-easing: report

Claude (Sonnet worker), 2026-11-13, branch `cc-easing`. Engine and tests only;
no device I/O, nothing written to the pad. `./test.sh` passed (361 tests)
before the commit and again after merging `main` (the merge brought only loom
renames).

## What I built

`glra_osc/engine.py`, built to `docs/config-app.md` §3.5–3.7. The clock stays
injected: time enters through `event.t` and `tick(now)`; nothing sleeps.

- **`tick(now)`** returns the glide messages due, at most one per (channel, cc),
  sent only when the rounded 7-bit value changed. A glide that has run its time
  sends exactly its target and ends. `tick` processes every running glide at
  `now`, whatever the time; it doesn't gate on `next_due`, so a late caller gets
  one catch-up message rather than a backlog.
- **`next_due()`** returns `t + 10 ms` when a glide starts on an idle engine,
  `now + 10 ms` after each tick while glides remain, and `None` when none do
  (including after a cancel or `release_all`).
- **Curves** (`CURVES`): linear, ease-in, ease-out, ease-in-out, the quadratic
  formulas of §3.6. Values round half up.
- **`cc-momentary`**: press glides to `high` over `rise-ms`, release to `low`
  over `fall-ms` (Bob, Q2), one `curve` for both. Each starts from the value
  last sent on that (channel, cc). Latch mode toggles the target the same way
  (rise on, fall off). A 0 ms direction jumps from `handle` and, as before,
  always sends.
- **`cc-step`**: target = running glide's target (else the sent value) + `step`,
  clamped 0..127; glides over `ease-ms` from the value last sent. Three quick
  +8 presses from 0 end at 24. At 0 ms it jumps and sends only on a change.
- **One glide per (channel, cc)**: a later glide, a `cc-set` or an absolute
  turn on the pair replaces it (set and dial win). Glides on other pairs, and
  the same cc on another channel, run independently. A glide whose target
  already equals the sent value starts nothing.
- **`release_all()`**: held `cc-momentary` jumps to `low`; every other running
  glide jumps to its target (message only if it differs from what was sent);
  latched CCs keep their value, as before.
- A layer change leaves running glides alone; a release still goes to the
  binding its press started.

## What I didn't build

- No runner wiring. `run` doesn't call `tick` yet; `runner-profile` has to
  schedule it from `next_due()` (and send what it returns). Until then the
  legacy adapter's mappings carry 0 ms everywhere, so nothing glides and `run`
  behaves as before.
- `cc-set` has no easing, as the design says (§2.3).

## Choices worth a look

- `tick` ignores `next_due` and always processes (see above). I chose this
  because float error in an accumulated 10 ms grid would otherwise skip ticks.
- A `cc-step` press at a clamp while a glide runs still retargets (full time
  again), the literal reading of §3.6. With no glide running it sends nothing.
- Ties round up (`floor(x + 0.5)`), not Python's banker's rounding, so curves
  are symmetric in a way a reader can predict.

## How I checked

`tests/test_glides.py` (31 tests), fake clock, no sleeping: the exact value
sequence at a 10 ms tick for each curve (0→100 over 100 ms, rising, and a
falling case), ends on target and goes idle, `next_due` through start, tick and
cancel, a late tick, no duplicate values, 0 ms jump, rise 0 with fall > 0,
separate rise and fall times, retarget mid-rise and mid-fall, latch toggling,
`cc-step` building, clamping and 0 ms behaviour, cancel by `cc-set` and by an
absolute dial, replacement by a later glide, independent ccs and channels,
layer change mid-glide, release to the starting binding, and `release_all`
cases. The first run found a real bug (a cancel left `next_due` set); fixed by
routing every cancel through `Engine._cancel`.

Not checked: real timing against the OS clock or a DAW; that waits for
`runner-profile` and the tour.

## Open questions

None for Bob; no `questions.md`.
