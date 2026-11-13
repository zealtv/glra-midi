# runner-profile — `glra-osc run` plays the profile, glides in time, reloads on change

Suggested model: Sonnet. Build to `docs/config-app.md`.

- `run` with no `--config` plays `profile.current_profile_path()` (design §2;
  Bob, 2026-11-13, Q7: the `current` pointer names the active profile in the
  profiles folder, and the helper creates `profiles/default.toml` from the
  shipped default when there is none). `--config FILE` plays that file; it
  reads profiles only (Bob, Q1: "we can hard break"), so drop "still accepts an
  old mapping file" from its help and the README.
- Switch `run` from mappings to profiles, and delete what that leaves unused:
  `runner.py`'s private `_profile_from_mapping` (the design-answers stitch
  moved the adapter there from `profile.py`, marked temporary), `mapping.py`,
  `default_mapping.toml` and their tests.
- Drive `Engine.tick` from the run loop while `next_due()` isn't `None` (100 Hz,
  `docs/config-app.md` §3.6), without busy-waiting when idle and without delaying pad
  events. Look at how `monitor.watch` blocks before choosing the mechanism.
- Reload when the profile file changes **or when `current` now names another
  profile** (mtime poll of both is enough; the app saves by rename, and
  Open… in the app calls `set_current`): `release_all()` (§3.7), swap the
  engine, keep the active layer if it still exists, else layer 1. An invalid
  file keeps the old profile and prints the error once. With `--config FILE`
  there is no pointer to follow; watch the file only.
- `--dry-run` prints layer changes and glide values too.
- Silencing, replug handling and exit behaviour stay as they are.
- README: the profile, layers, the new event kinds, hot reload.

Tests: reload swaps cleanly and releases held notes; a bad file is survived; the
tick driver emits a glide's values in order against a fake clock and port.
No pad needed; say in the report what only a real pad can show (for the tour).
