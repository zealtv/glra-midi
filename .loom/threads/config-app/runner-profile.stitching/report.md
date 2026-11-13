# runner-profile: report

Claude (Sonnet 5.5 worker), 2026-11-13, branch `runner-profile`. Built to
`docs/config-app.md` §2, §3.6–3.7. No device I/O; nothing written to the pad. `./test.sh`
(ruff + 341 unittests) passed before the commits; `main` had no new commits, so the merge
was "already up to date".

## What I built

- **`run` plays profiles.** No `--config`: `ProfileSource` follows
  `profile.current_profile_path()` (it creates `profiles/default.toml` when none exists).
  `--config FILE` plays that file, profiles only; the help text and README no longer
  mention mapping files. A `ProfileError` on the first load reaches the CLI (exit 2) before
  the port opens.
- **Deleted:** `glra_osc/mapping.py`, `default_mapping.toml`, `tests/test_mapping.py`, and the
  runner's `_profile_from_mapping`. Test and docstring mentions of them follow.
- **Tick driver.** `monitor.watch` gained `wake_at()` and `on_wake(now)`. The loop never
  sleeps past `wake_at()` and calls `on_wake(clock())` after each wait, after any queued
  report is handled, so a pad event never waits on a tick. `run` returns
  `min(engine.next_due(), next reload poll)` from `wake_at` and sends `engine.tick(now)` from
  `on_wake`. Idle (no glide) means the loop wakes only for the 0.5 s reload poll and its
  existing scan/tick schedule. A 1 µs slack (`TICK_SLACK`) stops float error in the 10 ms
  grid from skipping a tick (a test caught it: 0.05 + 0.01 > 0.06).
- **Reload.** Every 0.5 s `ProfileSource.poll` compares (path, mtime, inode, size); the path
  comes from `current` again, so a pointer switch counts. On change: `release_all()` through
  the port, a new `Engine` with the old layer (the engine falls back to 1 when the layer
  doesn't exist), `# reloaded <path>`. An invalid file keeps the old profile and prints
  `# profile not reloaded, keeping the old one: <error>` once per file version. With
  `--config`, only the file is watched.
- **`--dry-run`** prints layer changes (`# layer 1 -> 2 'Synth'`), each glide value (the MIDI
  lines it already printed), and, per the manager's note, each pad event labelled with the
  playing profile's orientation (`KEY 01 [key.13] DOWN` as in `monitor --profile`). The
  labels follow a reload. Normal (non-dry) runs print none of these event lines.
- README: profile, layers, event kinds, hot reload, dry-run labels.
- `lights` and `lighting.py` untouched.

## Not built / choices

- A changed `[midi] port` on reload is not applied: `run` keeps the open port and prints
  `# port stays 'X'; restart run to use 'Y'`. Reopening a virtual port mid-run would drop the
  DAW's connection; Claude's default, say if you want it otherwise.
- If the active profile file vanishes, `current_profile_path()` falls back to `default.toml`
  (recreated from the shipped one) and `run` reloads that. That follows §2's helper rules; I
  didn't add a "keep playing the deleted file" mode.
- Silencing, replug and exit behaviour unchanged (`on_lost`/exit still call `release_all` on
  the current engine).

## How I checked

`tests/test_runner.py` (rewritten, fake clock, fake `watch`, temp home): default profile
created and played; `--config` and the pointer; old mapping files refused before the port
opens; held notes released on exit, disconnect (once) and an exception; a glide's values come
out in order at 10 ms ticks and `wake_at` goes idle after; release mid-glide glides back; a
reload swaps cleanly and releases held notes and glides (never leaves a CC mid-glide); invalid
file survived and reported once, then a fixed file loads; vanished file; layer kept or reset;
pointer switch; `--config` ignores the pointer; port change noted; orientation labels (and
after reload). `WatchWakeTests` runs the real `watch` loop: `on_wake` fires on its schedule,
not the 0.25 s default wait, and after a queued report.

## Only a real pad can show (for the tour)

- Glide timing and smoothness against the real clock and a DAW (the 10 ms cadence under load).
- That key presses during a glide don't feel delayed; the loop design says they can't be, but
  nothing measured it.
- Hot reload while the app saves, and Open… switching profiles, with `run` live.
- That the orientation labels match how Bob holds the pad (the orientation stitch's open
  question).

## Open questions

None for Bob before the tour.
