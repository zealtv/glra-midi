# rename-places — the GitHub repo and the folder (with Bob)

Bob, 2026-11-13: rename "not only the repo - but also this repo folder". Needs
Bob present: it moves the working folder under any running session.

1. `gh repo rename glra-midi` on `zealtv/glra-osc` (GitHub redirects the old
   URL) and `git remote set-url origin https://github.com/zealtv/glra-midi.git`.
   Pushing main needs Bob's go-ahead (as of 2026-11-13 main sits ~90 commits
   ahead of origin).
2. End every Claude session in the repo and close tmux panes rooted there.
3. From outside: `mv ~/repos/glra-osc ~/repos/glra-midi`; optionally
   `mv ~/.claude/projects/-Users-bob-repos-glra-osc ~/.claude/projects/-Users-bob-repos-glra-midi`
   so session history follows (Claude Code keys it by path). The old worktree
   project dirs can go.
4. Rebuild the venv (its scripts hard-code the old path): `rm -rf .venv`,
   venv, `pip install -e '.[dev,gui]'`, `./test.sh`.
5. Check `~/repos/ai-kit/tools/repo-check ~/repos/glra-midi` and that
   `glra-midi run` still finds the moved profile folder.

## Progress (Claude, orchestrator, 2026-11-13 ~19:20 AEDT)

- Step 1 done: `gh repo rename` made `zealtv/glra-osc` into `zealtv/glra-midi`
  (still private); `origin` set to `https://github.com/zealtv/glra-midi.git`.
  Not pushed: main sat 119 commits ahead of `origin/main`; push waits on Bob.
- Before the rename, with Bob's go ("go with your suggestions"), local
  history from `ed2b147` on was rewritten to trim the crash report
  (`publication-audit.tied/questions.md`). Nothing rewritten had been pushed.
- Steps 2 and 3 belong to Bob: end the orchestrator session, close the worker
  panes (%29, %32, %46; all plain shells in the old folder), then from outside
  the folder move it, and the Claude project history if wanted.
- A fresh session in `~/repos/glra-midi` picks up at step 4: rebuild `.venv`,
  `./test.sh`, `repo-check`, run `glra-midi --version` and one real command to
  see the profile folder migrate (`glra-osc` → `glra-midi` under Application
  Support), then tie this stitch and go on to `first-release` with Bob.
- Small leftover from the audit: the tracked `inbox` symlink dangles in a fresh
  clone (`.nest/in/` has no tracked file). Harmless.

## Done (Claude, fresh session in ~/repos/glra-midi, 2026-11-13)

- Bob moved the folder and the Claude project history
  (`~/.claude/projects/-Users-bob-repos-glra-midi`; no `glra-osc` project dir left).
- Step 4: `.venv` rebuilt with python3.14; `./test.sh` passed (ruff, 590 tests OK);
  `glra-midi --version` printed `glra-midi 0.0.1`.
- Step 5: `repo-check` reported `ok`. `glra-midi lights` (read-only) printed
  the migration line and moved `~/Library/Application Support/glra-osc` to
  `.../glra-midi` (`profiles/default.toml`, `current` = `default`, backups, logs).
  The pad wasn't plugged in at the time ("found 0" interfaces), so no pad read
  got checked here.
