# app-review-polish: report (in progress)

Worker: Claude Sonnet 5.5, 2026-11-13. Items go one per commit, cheapest first:
13, 11, 10, 8, 9, 12, 5, then the pad view shrinking.

## Done so far

- **13** `lighting.data_dir` calls `profile.app_dir` (commit `0afb051`). Test: both agree.
- **11** The parser refuses `[key."01"]`, `layers."01"`, `"+1"` (a table name must be the plain
  number) and `version = 1.0`. The shipped default profile, `demo_profile.toml` and every file in
  `tests/fixtures/` still load (checked by loading them, not only by the suite). CHANGELOG
  "Changed" says what now fails.
- **10** An invalid port draft counts as unsaved (title bullet, quit/Open ask) and blocks Save and
  Save As with "Fix the MIDI port before saving: …". I chose blocking over "Save writes the old
  port" because the latter leaves the app dirty after a successful Save.
- **9** `Controller.poll` returns early while `_confirmed` or `_after` is pending. Stamps stay
  stale, so the change is noticed on the first poll after the answer.

## Left to do

8, 12, 5, then the pad view shrinking with the device panel open.
