# rename-code — report (worker, 2026-11-13)

## Built

- **Rename in the tree.** `glra_osc/` → `glra_midi/` (git mv); distribution
  `glra-midi`, commands `glra-midi` and `glra-midi-config`, `--version`
  (`glra-midi 0.0.1`), messages, window title, demo temp prefix, docs,
  README (clone URL `github.com/zealtv/glra-midi`), THIRD_PARTY_NOTICES,
  tests, `test.sh`, `tools/app-capture.sh`, and the current glean findings
  (index rebuilt).
- **AGENTS.md** line 3: "Named glra-osc until 2026-11-13, when Bob had it
  renamed"; also brought its status up to date (tour tied, public-release on
  the queue).
- **Application Support folder.** `APP_DIR_NAME = "glra-midi"`, plus
  `OLD_APP_DIR_NAME = "glra-osc"` and `profile.migrate_app_dir(home)`: when
  `glra-midi/` doesn't exist and `glra-osc/` is a folder, one `rename` in the
  same parent moves everything (profiles, `current`, backups, logs) and one
  line goes to stderr. Once moved, the new folder exists, so it never fires
  again. A failed rename prints a message and leaves both as they were.
  Called by every CLI subcommand (after argument parsing, so not on
  `--version`/`--help`) and by the app outside `--demo`/`--capture`.
  `docs/config-app.md` §2 records it as done.
- **silence.py**: checked, no change. Its entries count as "ours" by source
  code (the layout's codes mapped to no event), never by name, so a
  glra-midi build cleans up entries a glra-osc build left. Noted in
  `glean:keyboard-seize-needs-root`.
- **Test safety.** `tests/__init__.py` now points `HOME` at a throwaway
  folder for the whole test run, so no test (or subprocess it starts) can
  touch the real `~/Library/Application Support`. The one existing test that
  calls `cli.main` also patches the migration out.

## Left alone (as the stitch says)

History keeps the old name: `.lore/`, `.nest/`, every tied/dropped stitch
and the other live loom threads' notes (I didn't touch loom state or other
stitches' scope). The `glra-osc` occurrences that remain outside those
folders are deliberate: the dated AGENTS.md line, the README and design-doc
notes on the migration, `OLD_APP_DIR_NAME` and its tests, and two glean
lines that describe the past.

`glean:delegate-in-visible-tmux-panes` now gives the worktree path as
`../<repo-folder>-<stitch>`, so it holds before and after `rename-places`
moves the folder.

## How I checked it

- `./test.sh`: ruff clean, 585 tests OK (8 new in
  `tests/test_profile.py::AppDirMigrationTests`: full move and single
  message, nothing to move, existing new folder left alone, old path as a
  file, failed move, CLI moves on a command but not on `--version`, and the
  HOME guard). Run again after merging main: OK.
- The worktree `.venv` had the old `glra-osc` editable install; I
  uninstalled it and installed `-e '.[dev,gui]'` again. **Each existing venv
  (main's included) needs the same** (`pip uninstall glra-osc`, then
  `pip install -e '.[dev,gui]'`), or `glra-midi` won't exist and
  subprocess tests fail on `import glra_midi`.
- A fresh venv in the scratchpad with a non-editable `pip install '.[gui]'`:
  `glra-midi --version` printed `glra-midi 0.0.1`;
  `glra-midi config --demo --capture default --out …` exited 0 and rendered
  the app (`captures/fresh-venv-default.png`). `--capture main`, the name I
  tried first, doesn't exist; the states are listed by `--help`.
- Bob's real `~/Library/Application Support/glra-osc` was still there,
  unmoved, after every test run (checked by `ls`). No pad I/O.

## Heads-up for Bob and the manager

- The first time Bob runs any `glra-midi` subcommand or the app (not
  `--demo`) after this lands, his real `glra-osc/` folder moves to
  `glra-midi/`. An old `glra-osc` build still running or started later
  would then find no profiles and create a fresh `glra-osc/default.toml`.
- The version stays `0.0.1`; `release-process`/`first-release` set 0.1.0.

## Open questions

None blocking. No questions.md written.
