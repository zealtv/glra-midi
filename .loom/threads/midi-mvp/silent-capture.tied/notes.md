# silent-capture: done 2026-11-12 (agent run; hands-on check still open)

Route: the non-root hidutil mapping chosen in `suppression-route` (see its decision.md).
Code is in `glra_osc/silence.py`; the pieces:

- `Silencer.apply()` reads the current `UserKeyMapping` per service (`parse_mapping`,
  tested against real `--get` samples in `tests/fixtures/hidutil_get_*.txt`), removes
  any entries whose source is one of ours (leftovers from a killed run), appends our 25
  `(0x700000000|usage or 0xC00000000|usage) -> 0x700000000` entries (derived from
  `layout.json`), sets, re-reads, and checks every wanted entry on every service.
  It retries for 5 s when no services are listed yet or the verify fails.
  "Run as root" in the output, or a non-zero exit, is a failure (the root text fails at once).
- `Silencer.restore()` sets back exactly the saved original entries; `Silencer.unsilence()`
  (CLI `glra-osc unsilence`) removes entries by source, needs no saved state, and sets
  nothing when the pad is clean or absent.
- `monitor.watch(on_pad=...)` calls the hook each time the pad appears with both input
  interfaces enumerated, before any reader opens, and again after any interface was lost.
- `run` and `monitor` (both take `--allow-typing`) refuse with a reason and exit 1 when
  apply/verify fails; with `--allow-typing` they print a warning and go on. The old
  "pad still types" warning now shows only with `--allow-typing`. SIGTERM, Ctrl-C and
  normal exit restore (monitor gained a SIGTERM handler; run already had one).
- The hidutil call sits behind `Hidutil.run(*args)`; tests use a fake with the same
  text formats (`tests/test_silence.py`, plus runner tests).

Checked on the live pad (macOS 14.6, non-root, 2026-11-12, no keys pressed):
- `glra-osc run --dry-run` for 5 s: `--get` showed 26 entries on each of the 2 services
  (CapsLock→Cmd + our 25); after SIGTERM (exit 0) only the original CapsLock entry per
  service remained.
- `kill -9` left 52 `Src` lines (26 × 2); `glra-osc unsilence` removed 25 and left CapsLock
  (a second run says "nothing to remove"). A run started after a `kill -9` and stopped with
  SIGTERM ended with just CapsLock, so the leftover did not become the "original".
- Not run: a SIGINT from a real terminal (my background-job `kill -INT` was ignored by
  the shell; it shares the SIGTERM path), a replug, and any key press under the mapping.

## Still needs Bob's hands-on check (the stitch's own checklist)
- Replug the pad while `glra-osc run` runs: expect "# pad silenced" again, pad silent.
- Press keys and turn/push dials with the mapping on: nothing typed in TextEdit, Finder,
  a DAW (modifiers held too), no volume change; MIDI still arrives. Only the original
  stock-capture trial covered the dials (`suppression-route` decision.md); this layout's
  F13–F24, `0x46–0x49` and consumer E3–F2 codes were not yet pressed under the mapping.
- Built-in and other keyboards unaffected; CapsLock→Cmd on the pad still works while running.
- Ctrl-C in a real terminal restores; after `kill -9` the pad stays silent until
  `glra-osc unsilence` or a replug.
- `glra-osc monitor` refuses/continues as expected with a failing apply (hard to provoke
  by hand; covered by unit tests only).

## Known limits
- Services with different mappings are merged as a union and restored to that union
  (the pad's two services carried identical ones on 2026-11-12).
- Verify covers the services hidutil lists at that moment; `watch` only calls the hook
  once both input interfaces are enumerated, to avoid a half-covered pad.
- A source that Bob already maps on this pad (e.g. F13) would be replaced by ours while
  running and removed by `unsilence`; none exist as of 2026-11-12.
