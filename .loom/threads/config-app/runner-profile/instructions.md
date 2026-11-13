# runner-profile — `glra-osc run` plays the profile, glides in time, reloads on change

Suggested model: Sonnet. Build to `docs/config-app.md`.

- `run` with no `--config` loads the user's profile if it exists (path from the
  design), else the shipped default; `--config FILE` still works and still
  accepts an old mapping file.
- Drive `Engine.tick` from the run loop while `next_due()` isn't `None` (the
  design's tick rate), without busy-waiting when idle and without delaying pad
  events. Look at how `monitor.watch` blocks before choosing the mechanism.
- Reload when the profile file changes (mtime poll is enough): release what's
  held, swap the engine, keep the active layer if it still exists. An invalid
  file keeps the old profile and prints the error once.
- `--dry-run` prints layer changes and glide values too.
- Silencing, replug handling and exit behaviour stay as they are.
- README: the profile, layers, the new event kinds, hot reload.

Tests: reload swaps cleanly and releases held notes; a bad file is survived; the
tick driver emits a glide's values in order against a fake clock and port.
No pad needed; say in the report what only a real pad can show (for the tour).
