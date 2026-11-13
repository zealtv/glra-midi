# design-answers: report

Claude (Sonnet worker), 2026-11-13. The first worker paused part-way (Q1 in code, the doc done);
a second worker session resumed the same day and finished. The stitch is done on branch
`design-answers`. `main` is merged in, and `./test.sh` passes (330 tests, ruff clean) after the merge.

## What I built

- **Q1, hard break** (first worker, `d7b8188`). `profile.py` no longer loads old mapping files: no
  `is_legacy_mapping`, no `profile_from_mapping`, and a file without `version` fails with
  `version: required; ...`. `run` still needs the adapter, so it lives on as a private,
  temporary `_profile_from_mapping` in `runner.py`; `runner-profile` deletes it. Engine tests
  build profiles from TOML. `NoLegacyTests` replaces `LegacyTests`.
- **`docs/config-app.md`** (first worker, `c79ca96`): §2, 2.1, 2.3, 2.5, 2.6, 2.7, 3.5, 3.6, 4.3,
  4.4, 4.5, 4.8 and 7 follow Q1, Q2, Q3 and Q7. I left the doc alone this session.
- **Q2, rise and fall.** `CcMomentary` has `rise_ms` and `fall_ms` (0..10000, default 0) in place
  of `ease_ms`; `cc-step` keeps `ease-ms`. `ease-ms` on `cc-momentary` is now an
  "unknown key" error. Tests cover the round trip, the range, and the removed key.
  `DESIGN_EXAMPLE` follows §2.5 (`rise-ms = 250`, `fall-ms = 600`).
- **Q3, default profile.** `default_profile.toml` rewritten to §2.7: 3 layers; dial pushes
  `layer-set` 1, 2, 3; keys per-layer notes 36..51 with channel = layer; `enc.1.turn` and
  `enc.2.turn` per-layer `cc-relative` CC 16 and 17 with channel = layer; `enc.3.turn` global
  `cc-absolute` CC 18, channel 1, initial 64. The format comment at its head now documents
  `rise-ms` and `fall-ms`. `DefaultProfileTests` rewritten to match.
- **Q7, profiles folder and pointer.** In `profile.py`: `app_dir`, `profiles_dir`,
  `profile_path(name)`, `check_profile_name`, `current_profile_path`, `set_current(name)` (each with
  an optional `home`), plus a shared `_write_atomic` that `dump_profile` and `set_current` use.
  `user_profile_path` and `PROFILE_FILE_NAME` are gone; `lighting.py`'s `lights_command` now uses
  `current_profile_path()`. `ProfileFolderTests` cover a fresh home, following the pointer,
  every fallback (empty, invalid, missing file) keeping the pointer untouched, an existing
  `default.toml` never overwritten, `set_current` (valid, missing, bad name, no temp file left).
- **Later stitches' `instructions.md`**: `cc-easing` (rise over `rise-ms`, fall over `fall-ms`),
  `runner-profile` (play `current_profile_path()`, reload when the file or `current` changes, delete
  the temporary adapter, `mapping.py`, `default_mapping.toml` and their tests, drop "old mapping
  file" from `--config`), `app-shell` (§4.8 file behaviour, no legacy notice), `config-app-review`
  (checks the pointer and that old mapping files fail cleanly).

## What I didn't do

- No engine change: glides belong to `cc-easing`, so the engine still jumps for every time.
- No `loom:` or glean notes. Nothing here seemed to earn a glean finding beyond the design doc.
- I left mentions of `user_profile_path` and `profile.toml` in the completed `profile-model.tied` and
  `config-design.tied` notes; they record what was true when those stitches ran.

## How I checked

`./test.sh` (ruff plus unittest), run after each code step and again after merging `main`. No
device I/O and no pad writes; all tests use fakes or temp directories as `home`.
`lights_command` with no `--profile` now calls `current_profile_path()`, which creates
`profiles/default.toml` in the real home on first use; the lighting tests always pass a path or mock the
device, so none of them touched the real home folder (not verified beyond reading the test code).

## Differences from the stitch text

- The stitch says `cc-set` keeps an `ease-ms`. The design (§2.3) gives `cc-set` no easing; only
  `cc-step` has it. I followed the design, which the brief says wins.

## Open questions for Bob

None blocking, and none written to `questions.md`. Readings of his Q7 answer I took (he may want them
changed):
- `current` holds a profile *name* (the file stem), not a path.
- Open… sets the pointer, so `run` follows the app.
- The app opens only files in `profiles/`; renaming and deleting profiles go on the tour's "later" list.
- A missing pointer is written (as `default`) the first time `current_profile_path()` runs; an existing
  pointer, even an invalid one, is left alone and only falls back for that call.

Orchestrator, 2026-11-13 15:16 AEDT: landing waits for the rest; the branch stays in
`../glra-osc-design-answers`, claimed.
