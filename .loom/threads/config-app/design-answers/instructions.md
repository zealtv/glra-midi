# design-answers — apply Bob's answers to the design questions

Suggested model: Sonnet. Fix stitch, shaped by the orchestrator on 2026-11-13
from Bob's answers (`lore:2026-11-13-config-design-answers`; the answers and
the readings taken sit under each question in
`config-design.tied/questions.md`). Read both first.

Change `docs/config-app.md` first, then the code to match, then the later
stitches' `instructions.md` where they mention what moved:

1. **Q1, hard break.** Drop legacy mapping loading from the profile (no
   `is_legacy_mapping`, `profile_from_mapping`, §2.6). `run` still reads a
   mapping until `runner-profile`; leave `mapping.py`, `default_mapping.toml`
   and the runner as they are, and tell `runner-profile` (its instructions) to
   delete them when it switches `run` to profiles. Port the engine tests that
   use `profile_from_mapping` to build profiles directly (or parse TOML).
2. **Q2, separate rise and fall.** `cc-momentary` gets `rise-ms` and
   `fall-ms` (default 0) in place of one `ease-ms`; one `curve`. Update the
   schema, parser, writer, tests, §2.3/§3.6, and `cc-easing`'s instructions.
   Other eased kinds (`cc-set`, `cc-step`) keep one `ease-ms`.
3. **Q3, default profile.** Rewrite `glra_osc/default_profile.toml` and §2.7
   to the reading in `questions.md`.
4. **Q7, profiles folder and pointer.** `profiles/` under the app directory
   (`APP_DIR_NAME`) and a `current` file naming the active profile; helpers
   `profiles_dir()`, `current_profile_path()` (falls back to creating
   `profiles/default.toml` from the shipped default), `set_current(name)`.
   Update §2 and the app's file section (§4.8: Open…/Save As… work within
   the folder; the window title names the profile), and the instructions of
   `runner-profile` (run plays the current profile and reloads when it, or the
   pointer, changes) and `app-shell`.

Done when: the doc, `profile.py`, the default profile and the later stitches
agree with Bob's answers, and `./test.sh` passes.
