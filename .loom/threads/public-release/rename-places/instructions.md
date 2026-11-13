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
