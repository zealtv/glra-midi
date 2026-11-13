# design-answers: report (paused part-way)

Claude (Sonnet worker), 2026-11-13. The manager asked me to pause because usage was near its limit.
I stopped at a clean commit. **The stitch is not done**: Q1 is finished; Q2, Q3 and Q7 have
their doc text but no code yet.

## Where I stopped

`./test.sh` passed (317 tests) at commit `d7b8188`. The later doc-only commit `c79ca96` touches
no code, and I did not rerun the tests after it. I did **not** merge `main` into the branch;
the manager should merge it, since I didn't check for conflicts.

## Done

- **Q1, hard break (code, `d7b8188`).**
  - `glra_osc/profile.py`: removed `is_legacy_mapping`, `profile_from_mapping`, the legacy
    branch of `parse_profile` and the `mapping` import. A file without `version` now fails with
    `version: required; a profile starts with 'version = 1' (old mapping files no longer load)`.
  - `glra_osc/runner.py` imported `profile_from_mapping`, and the stitch says to leave the
    runner alone. To keep `run` working I moved the adapter into `runner.py` as a private
    `_profile_from_mapping`, marked temporary. `runner-profile` should delete it along with
    `mapping.py` and `default_mapping.toml`.
  - `tests/test_engine.py` now builds profiles from TOML text (`engine(text)`, plus a
    one-layer "old default" helper). `tests/test_profile.py`: `LegacyTests` replaced by
    `NoLegacyTests` (no `version` is an error; the old default mapping doesn't load).
- **`docs/config-app.md` for Q1, Q2, Q3 and Q7 (`c79ca96`).**
  - Rewrote §2 (folder, `current` pointer, helper behaviour), §2.1 (`version` row), §2.3
    (`rise-ms` and `fall-ms`), §2.5 (example), §2.6 (old mapping files), §2.7 (default profile),
    §3.5 and §3.6 (glide durations), §4.3 (title), §4.4 (summary text), §4.5 (inspector), §4.8
    (files) and §7 (where each of Bob's answers landed).

## Left to do

1. **Q2 in code.**
   - In `profile.py`, `CcMomentary` takes `rise_ms` and `fall_ms` (0..10000, default 0) in place
     of `ease_ms`, in the dataclass and the `_SPECS` entry. The `ease-ms` field stays on `cc-step`.
   - Update `tests/test_profile.py`, including `DESIGN_EXAMPLE` (still `ease-ms = 250` on
     `cc-momentary`) and the `CcMomentary(... ease_ms=...)` uses.
   - Reword `cc-easing/instructions.md`: a press glides over `rise-ms`, a release over `fall-ms`;
     `cc-step` uses `ease-ms`.
2. **Q3.** Rewrite `glra_osc/default_profile.toml` to match §2.7:
   - 3 layers; `enc.N.push` = `layer-set` N.
   - Keys are per-layer notes 36..51 with channel = layer.
   - `enc.1.turn` and `enc.2.turn` are per-layer `cc-relative` CC 16 and 17 with channel = layer.
   - `enc.3.turn` is a global `cc-absolute` CC 18, channel 1, initial 64.
   - Then fix `DefaultProfileTests` in `tests/test_profile.py`.
3. **Q7.**
   - In `profile.py` add `app_dir()`, `profiles_dir()`, `current_profile_path()` and
     `set_current(name)`, each with an optional `home`, with the behaviour in §2. Factor an
     atomic-write helper out of `dump_profile`.
   - Remove `user_profile_path` and `PROFILE_FILE_NAME`. `lighting.py` `lights_command` uses
     `user_profile_path`, so switch it to `current_profile_path()` and replace `test_paths`.
   - Add tests for the fallback, the invalid-name check, and that an existing pointer is never
     rewritten.
4. **Later stitches' instructions.**
   - `runner-profile`: play `current_profile_path()`; reload when the file or `current` changes;
     delete `runner.py`'s `_profile_from_mapping`, `mapping.py`, `default_mapping.toml` and
     their tests; drop "still accepts an old mapping file" from `--config`.
   - `app-shell`: use the profiles folder and pointer (§4.8); drop "opening a legacy mapping
     says...".
   - `config-app-review`: its text mentions "legacy loading".
5. Merge `main`, rerun `./test.sh`, and finish this report.

## Differences from the stitch text

- The stitch says `cc-set` keeps an `ease-ms`. The design (§2.3) and `profile.py` give `cc-set`
  no easing, only `cc-step` has it. I followed the design, as the brief says it wins.
- I haven't written `loom:` notes or any glean finding.

## Open questions for Bob

None new. These are readings of his Q7 answer that I took; he may want them changed:
- `current` holds a profile *name* (the file stem), not a path.
- Open… sets the pointer, so `run` follows the app.
- The app opens only files in `profiles/`.
Renaming and deleting profiles in the app go on the tour's "later" list.

Orchestrator, 2026-11-13 15:16 AEDT: landing waits for the rest; the branch
stays in `../glra-osc-design-answers`, claimed. Resume plan in
`.groundhog/schedule/once/2026-11-13/16-15/resume-config-app-orchestrator/prompt.md`.
