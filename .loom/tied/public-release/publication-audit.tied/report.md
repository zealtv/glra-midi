# publication-audit — report

Claude (Opus worker), 2026-11-13.

## What I did

- Read every commit on every ref (`git log -p --all`, 157 commits at the
  first pass, then the five `release-process` commits merged from `main`),
  every blob's path and size (725 blobs, largest 217 KB), image metadata, all
  six board photos, a sample of the app screenshots, and the dumps, backups,
  captures and logs, deleted ones included.
- Wrote `audit.md`: ten findings with commits, paths and options. None
  needs a history rewrite, in Claude's judgement. No credentials, no
  third-party personal details, no vendor firmware or copied pages.
- Fixed in the tree (`536430a`), as the stitch allows for clearly-right
  tree-only fixes: SPDX lines on `test.sh`, `tools/app-capture.sh`,
  `glra_midi/device/__init__.py`; `tomli-w` (MIT) added to the dependency
  table in `THIRD_PARTY_NOTICES.md`.
- Wrote `questions.md`: five decisions for Bob, each with the default taken.

## What I didn't do

- No history rewrite, no removals: those choices belong to Bob.
- Didn't touch the board photos (Bob: "keep the photos").
- Didn't add SPDX lines to the profile TOMLs, the tied research scripts in
  `.loom`, or the primitives' scripts (reasons in `audit.md` F9 and F5).
- Didn't redact the crash report (F1) or the vendor contact (F2): both left
  for Bob (questions 3 and 4).
- Didn't audit the shared stash stack or the main checkout's reflog; a push
  doesn't publish them.

## How I checked it

- Pattern scans over the full patch text: credential shapes, emails, phone
  numbers, `/Users/` paths, URLs (every domain listed and the odd ones read in
  context), other repos' names, personal words, capitalised name pairs.
- `exiftool` on all JPEGs and PNGs; `mdls` on the JPEGs.
- Parsed the raw HID captures to list every typed character and device path.
- `./test.sh` after the fix and again after merging `main`: 417 tests, OK
  (4 skipped: the four app test modules, as this worktree's venv has no PySide6; none of today's changes touch the app).

## Open questions

See `questions.md` (primitives' licence; whether the `zealtv/*` repos are
public; crash-report IDs; vendor contact in lore; any rewrite at all).
