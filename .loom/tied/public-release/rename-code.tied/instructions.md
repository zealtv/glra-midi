# rename-code — glra-osc becomes glra-midi inside the repo

Bob, 2026-11-13: rename the repo and "this repo folder so everything is
consistent". This stitch does everything that lives in the tree; the GitHub
repo and the folder move come in `rename-places`.

- Distribution `glra-midi`, package `glra_midi`, commands `glra-midi` and
  `glra-midi-config`, `--version` text, messages, docs, README, AGENTS.md,
  THIRD_PARTY_NOTICES, tests, tools, current glean findings.
- `profile.APP_DIR_NAME` → `glra-midi`. Per Q9 (Bob, "sounds good"): on first
  start, if `~/Library/Application Support/glra-midi` doesn't exist and
  `glra-osc` does, move it (profiles, `current`, backups, logs) and say so
  once; tested with a temp home, never Bob's real folder.
- Check how `silence.py` recognises its own hidutil entries; if the name enters
  into it, a new build must still clean up entries an old build left.
- Leave history alone: lore items, tied/dropped stitches and nest receipts keep
  the old name as written then. Add one dated line to AGENTS.md: "named
  glra-osc until 2026-11-xx".
- README clone URL → `github.com/zealtv/glra-midi`.
- No pad writes (thread rules). `./test.sh` passes; a fresh venv install runs
  `glra-midi --version` and `glra-midi config --demo --capture`.
