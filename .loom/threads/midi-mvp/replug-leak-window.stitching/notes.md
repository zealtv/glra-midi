# replug-leak-window: notes (2026-11-12, agent, Sonnet 5.5)

## Changed
- `glra_osc/silence.py`: new constants `FAST_CHECK_SECONDS = 0.1` and `FAST_WINDOW_SECONDS = 10.0`
  next to `CHECK_SECONDS = 2.0`, plus `check_interval(since_connect)` (fast inside the window, slow after).
- `glra_osc/monitor.py` `watch`: after each `on_pad` it records `connected_at`; `on_tick` runs on
  `check_interval`'s schedule, so every reconnect restarts the 10 s fast window. The old fixed
  `events.get(timeout=0.25)` would have capped ticks at 4 Hz, so the wait is now
  `min(0.25, time to next scan or tick)` through a small `_next_event` helper. `watch` takes an
  injectable `clock` (default `time.monotonic`).
- `tests/test_silence.py` (`CheckCadenceTests`, `FakeTime`): interval function; `watch` ticks every
  0.1 s for 10 s then every 2 s; a reconnect restarts the fast window; a simulated macOS
  overwrite at t = 0.3 s is repaired by the next 0.1 s tick, with CapsLock kept and exit leaving
  exactly CapsLock; one `hidutil --get` per tick when nothing is missing. No real sleeps.
  `./test.sh` passes (153 tests, ruff clean).
- `README.md`: stale "no MIDI output yet" status replaced; usage added for `run` (`--dry-run`,
  `--allow-typing`, `--config`), `monitor` (`--raw`), `unsilence`, checked against `cli.py`/`mapping.py`.
  There is no default user config path: without `--config`, `run` uses the shipped
  `glra_osc/default_mapping.toml`.

## Measured (2026-11-12, macOS 14.6, Bob's pad on this machine, no replug)
- **The race itself: not measured.** The pad stayed connected the whole session. A read-only
  poller (`/tmp/glra-scratch/poll_mapping.py`, 20 ms `hidutil --get`, log
  `/tmp/glra-scratch/poll.log`, scheduled to run until about 22:15) saw no service change apart
  from my own self-check sets. So the actual delay between connect and macOS's overwrite is
  still unknown; the "~0.3 s" in the unit test is an assumption, not a measurement. Bob's
  2026-11-12 acceptance run only showed that the overwrite lands before the old 2 s re-check.
- Cost: `hidutil property --get` took 4.7 ms min / 4.8 ms median / 8.9 ms max over 50 runs
  (subprocess wall time). Polling every 100 ms for 10 s is about 100 spawns, roughly 5% of one core
  for 10 s, then back to one every 2 s.
- Self-check without replug (`/tmp/glra-scratch/selfcheck.py`, `glra-osc run --dry-run`, two
  runs): our 25 entries were on both services 0.09 s after start; overwriting the pad with
  CapsLock-only 1.1 s after start was repaired in 0.11 s (both runs); overwriting at about 12.6 s
  (slow path) was repaired in 1.5 s and 1.6 s (inside the 2 s tick). SIGTERM left exactly the one
  CapsLock entry (Src 0x700000039 -> Dst 0x7000000E3) on both services, exit code 0. A separate
  hand run with overwrites every 1 s saw a "reapplied" log line for each. (In the self-check
  script one "reapplied" line went missing because the script sent SIGTERM within ms of the
  repair; it looks like a script artefact, not a bug.)
- The pad ends this session with the CapsLock entry only (2 services, 1 entry each).

## Not done / needs Bob
- **Replug test (needs Bob):** start `glra-osc run`, unplug and replug the pad, then press keys 2
  and 16 repeatedly for 5 s with the runner pane focused. Nothing may type (no `ESC[1~`, no
  brightness change). If something still leaks, the next step is the second idea in the
  stitch: delay the first apply until macOS's own entry appears. That needs the real
  connect-to-overwrite timing, which the poller can record if run during a replug:
  `python3 /tmp/glra-scratch/poll_mapping.py 120` (read-only), or the same script kept from the scratch dir.
- The delay-first-apply idea was not tried: nothing measured yet shows it is needed.
- Even at 100 ms a key pressed in the first ~100 ms after connect, before our first apply
  finishes, can still type; the window is smaller, not zero.
- `glean:keyboard-seize-needs-root` revised (fast re-check window; race timing still unmeasured).
