# release-process — report (worker, 2026-11-13)

## Built

- **Version in one place.** `__version__` in `glra_midi/__init__.py` stays the source;
  `pyproject.toml` now has `dynamic = ["version"]` with `[tool.setuptools.dynamic]
  version = { attr = "glra_midi.__version__" }`. `glra-midi --version` already read it. The
  version stays `0.0.1`: the stitch leaves the 0.1.0 bump to `first-release`.
- **`CHANGELOG.md`** (Keep a Changelog). `[Unreleased]` holds the 0.1.0 content (Added,
  Changed, Known limits), drafted from the README, the config-app tour and the tied stitches
  `midi-mvp` and `config-app`. I wrote it from those documents, not from the pad; Bob should
  read it before it becomes the 0.1.0 section.
- **`docs/releasing.md`**: who decides (tag, push, GitHub release and visibility each need
  Bob's go-ahead every time), the versioning rules (SemVer; 0.x minor may break the profile
  format or CLI), a section on the profile file's own `version = 1`, the numbered release
  steps (changelog, version commit, `release-check.sh`, push and tag, `gh release create`
  with the wheel and sdist, no PyPI) and how to install a release.
- **`tools/release-check.sh <version>`**: clean tree on main and tag free; `./test.sh`;
  `__version__` and `## [X.Y.Z] - date` match; `python -m build` of `git archive HEAD` in a
  temp venv; wheel and sdist both hold LICENSE and THIRD_PARTY_NOTICES.md (the wheel also the
  default profile, `layout.json`, `Main.qml`); a fresh venv installs the wheel and
  `glra-midi --version` prints `glra-midi X.Y.Z`. Copies the two files to `dist/`
  (git-ignored). It never tags or pushes. `--allow-any-branch` skips only the "on main"
  check, for rehearsal.
- **`tests/test_release.py`** (5 tests): version is plain SemVer; pyproject takes it
  dynamically from the package; the `__version__` line matches the pattern the script greps;
  the changelog has an `Unreleased` section and dated SemVer headings.
- **Glean:** new finding `release-process`; index rebuilt. **README:** a short "Releases"
  section pointing at the changelog and `docs/releasing.md`.

## Not done

- No version bump, tag, push, GitHub release or repo change (all Bob's; `first-release`).
- The script's step 1 on a real `main` checkout has not run; only the failure message ran
  (below). The rest ran on the branch with `--allow-any-branch`.
- No GUI extra in the fresh-install step (PySide6 is large); the `config` command's start-up
  runs under `./test.sh`, and rename-code's fresh-venv capture covers the `gui` install.
- `docs/config-app.md` §2 (profile format) doesn't yet say when `version` bumps; the rule
  sits in `docs/releasing.md` only.
- Loom state, queue and other stitches untouched.

## How I checked it

- `./test.sh`: ruff clean, 590 tests OK (585 from rename-code, plus 5 here), after merging
  main (which only changed loom claim files). The worktree `.venv` had no PySide6 at first
  (417 tests, four app modules skipped); I installed `-e '.[dev,gui]'` so the full suite runs.
- **Rehearsal** in a throwaway clone of the branch (version set to 0.1.0 and a dated
  changelog section added there only): `tools/release-check.sh --allow-any-branch 0.1.0`
  passed all six steps in about 9 s and printed `glra-midi 0.1.0`. Output in
  `rehearsal.txt` here. The files in the clone's `dist/` are not kept.
- **Failure cases**, same clone: wrong version (`0.1.1`) stopped at step 3; `abc` and `1.0`
  rejected as not X.Y.Z; running without the flag on a non-main branch stopped with "on
  'release-process', not main"; an untracked file stopped on "working tree is not clean"; an
  existing tag `v0.1.0` stopped with "tag v0.1.0 already exists"; a changelog heading
  without the exact form stopped with "no '## [0.1.0] - YYYY-MM-DD' section".
- Not exercised: a failing `./test.sh` or build inside the script (the paths print the log
  tail and fail; read, not run).

## Open questions (none block; defaults taken)

1. **Profile-format bump rule** (`docs/releasing.md`, "The profile format's own version"):
   bump `version` when an old file stops loading or changes meaning; not for a new optional
   key. My proposal, marked so in the doc. Bob to confirm or correct.
2. **0.1.0 changelog wording.** Bob reads `[Unreleased]` before `first-release`.
3. **Release steps use `gh release create`** and `git push origin main` literally; if the
   remote has another name or the repo publishes from a branch other than `main`, the doc
   changes then. The README names `github.com/zealtv/glra-midi` as the clone URL (from
   rename-code); I didn't check that the repo exists under that name.
4. The first commit on this branch (`0276563`) lacks the Co-Authored-By trailer; later ones
   carry it.
