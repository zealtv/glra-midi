# Publication audit: what the whole history makes public

Claude (Opus worker on `publication-audit`), 2026-11-13, for Bob's decision
before the repo goes public with full history ("i'd like the research done here
to be public", Bob, 2026-11-13).

## What was read

As of branch `publication-audit` at `202f623` (main at `48e6c4b` plus the
claim), every ref (`main`, `publication-audit`, `release-process`,
`origin/main`). `main` moved to `a817606` during the audit (`release-process`
tied: five commits, `0276563`..`a817606`); those were merged in and scanned
the same way, with nothing found.

- 157 commits at the first pass (160 with `release-process`), 2026-11-12 to
  2026-11-13, one author and committer:
  `Bob Jarvis <bob@zeal.co>`. 145 commits also carry
  `Co-Authored-By: Claude … <noreply@anthropic.com>` and a `Claude-Session:` link.
- 956 paths ever committed; 503 in today's tree; 453 since moved or deleted
  (mostly `.loom` stitch renames: `foo` → `foo.stitching` → `foo.tied`, and
  `glra_osc/` → `glra_midi/`).
- 725 distinct blobs, 8.7 MiB uncompressed; pack 3.5 MiB.
- Method: `git log -p --all` (8.7 MB of text) searched for credential shapes
  (API keys, `ghp_`/`sk-`/`AKIA`/`xox`, PEM headers, `token`/`secret`/`passw`),
  email addresses, phone numbers, home paths, URLs, other repos' names, other
  people's names and personal words; every image's metadata read with
  `exiftool`; all six board photos and a sample of screenshots looked at;
  the dumps, backups, captures and logs (including deleted ones) opened.

Not covered: the stash stack (shared with other worktrees, not pushed by
`git push --all`), and refs that exist only in the main checkout's reflog.
Neither gets published by a normal push.

## Summary

Nothing found needs a history rewrite, as far as this audit saw. No
credentials, tokens or keys turned up anywhere in history. No other person's
personal details. No vendor firmware, flash images, datasheets or copied web
pages. The largest blob is 217 KB. The findings below are small and each has
an "accept" option. The ones most worth a look: F1 (machine identifiers in a
crash report) and F2 (a vendor's phone number that `call-for-chip-info` kept
out of the public doc but lore keeps).

Severity, as Claude judged it: **low** = could reasonably go public as is;
**info** = noted so the choice is a conscious one.

## Findings

### F1 — macOS crash report carries machine identifiers (low)

- Path: `.loom/threads/patch-0.1.1/evidence/quit-crash-184200.ips` (37 KB),
  added in `ed2b147` (2026-11-13, tour answers).
- What it holds: `crashReporterKey` (`(redacted)`, a stable per-Mac anonymous
  ID Apple uses to group a machine's crash reports), `storeInfo.deviceIdentifierForVendor`,
  `incident`/`sleepWakeUUID`, model `Mac14,2`, macOS 14.6.1 (23G93), uid 502,
  uptime, the terminal (Ghostty) and shell, timestamps in +11:00. User paths
  were already redacted by macOS (`/Users/USER/*`).
- Risk: these IDs don't name Bob, but `crashReporterKey` would let anyone link
  this machine to other crash reports Bob ever posts publicly.
- Options:
  1. **Accept** (the IDs alone identify nothing).
  2. **Tree only:** replace the two stable IDs with zeros. History keeps them,
     so this only helps if F1 is the only reason to care.
  3. **Rewrite history** (`git filter-repo --blob-callback` or `--replace-text`
     on the two values in that one file). One file in one commit, but every
     later commit hash changes.
- Claude's suggestion: 1, or 3 if Bob is rewriting history anyway.

### F2 — a vendor's phone number and email kept in lore and loom (low)

- Paths: `.lore/items/2026-11-13-further-chip-findings-m9f9520/content/report.md`
  (lines 62, 64), `.loom/threads/custom-firmware.waiting/firmware-approaches/instructions.md`
  (line 53), `.glean/findings/k16n3-firmware-replacement.md` (lines 22, 48),
  plus `item.md` and receipts. Commits `19faa3c`, `1b23347` (2026-11-13), and
  the deleted raw arrival `.nest/in/further-chip-findings.txt`.
- What: Masses Chip's customer-service email `cs@masses-chip.com` and phone
  `+86 551 65336515`, as ChatGPT's report gave them (both from the vendor's own
  contact page).
- Why it's noted: `call-for-chip-info` took the default of keeping "Masses
  Chip's email and phone number … out of the public doc" (its report,
  2026-11-13), and left the choice to Bob. The lore copy keeps both, so the
  repo going public publishes them anyway.
- Risk: it's a company's published business contact, not a person's. Low.
- Options: 1. **accept** (lore keeps sources whole; the contact is public);
  2. tree-only removal from glean/loom (lore stays whole by its contract, so
  the number stays in the tree regardless); 3. rewrite history to redact it
  from lore too.
- Claude's suggestion: accept. Answering the `call-for-chip-info` question
  either way settles both.

### F3 — `Claude-Session:` links in 145 commit messages (info)

- Every agent commit carries `Claude-Session: https://claude.ai/code/session_…`.
- These URLs need Bob's claude.ai login to open, so they publish an ID, not
  the session. They also show the work was agent-driven, which the repo says
  openly anyway (`AGENTS.md`, the loom).
- Options: accept; or rewrite history (`git filter-repo --message-callback`)
  to strip the trailer. Rewriting touches every commit.
- Claude's suggestion: accept.

### F4 — Bob's other private projects named, not their contents (info)

As of this audit the tree and history name, without quoting their contents:

| Name | Where (examples) | What's said |
|---|---|---|
| `qtable` | `glean:delegate-in-visible-tmux-panes`, `.loom/threads/config-app/orchestrator.md`, `lore:2026-11-13-config-app-brief` | a peer repo whose worker process this repo copies; paths to its glean findings |
| `tengu-the-gremlin` / Tengu | `.lore/items/2026-11-13-k16n3-board-photos/content/album-*/request.md`, `.nest/dropped/…` | Bob's Telegram relay that delivered the photos; inbound item IDs |
| `ai-kit` (`tools/claude-usage`, `tools/repo-check`) | `glean:delegate-in-visible-tmux-panes`, `orchestrator.md`, `rename-places/instructions.md` | tool paths under `~/repos/ai-kit` |
| `easyloom` | deleted groundhog prompt (`d2e4b54`, removed in `8239582`) | a tmux pane name |
| `glean`, `loom`, `lore`, `nestlings`, `groundhog` | READMEs in the dotdirs | `https://github.com/zealtv/<name>` links |

Plus operational detail about Bob's Claude plan ("don't go over 92% of the 5
hourly usage window", tmux pane IDs) in `glean:delegate-in-visible-tmux-panes`
and the deleted groundhog prompt.

- Risk: names and paths only. If any `zealtv/*` repo above is still private,
  the public README links will 404 for readers (not a leak).
- Options: accept; or tree-only rewording of glean/loom notes (history keeps
  the names).
- Claude's suggestion: accept. See questions.md Q2 on the `zealtv` links.

### F5 — the primitives' scripts have no licence of their own (info, GPL)

- `.glean/glean.sh`, `.loom/loom.sh` (100 KB), `.lore/lore.sh`,
  `.nest/nestling.sh`, `.groundhog/groundhog.sh` and their READMEs come from
  Bob's `zealtv/{glean,loom,lore?,nestlings,groundhog}` repos. None carries an
  SPDX line or licence notice here, and `THIRD_PARTY_NOTICES.md` doesn't
  mention them.
- Effect: published inside a GPL-3.0-only repo with no marking, a reader would
  take them as GPL-3.0-only too. They are Bob's own work, so there's no rights
  problem; the question is only whether Bob wants them read as GPL.
- Options: accept (they read as GPL here); or add a line to
  `THIRD_PARTY_NOTICES.md` naming their upstream and licence (tree only).
  Adding SPDX lines inside the scripts would diverge them from upstream, which
  the primitives' update path (copy the script over) would then clobber.
- Claude left this to Bob: questions.md Q1.

### F6 — `.gitignore` says device data stays out of git; research captures went in (info)

- `.gitignore` (since `2fbcdb9`): "Device data is private; keep captures and
  logs out of git" (ignores `dumps/`, `backups/`, `logs/`, `*.log`).
- Committed anyway, as research evidence: raw HID captures
  (`.loom/tied/midi-mvp/raw-report-capture.tied/captures/*.jsonl`, `46c8638`),
  hidutil mapping dumps, the pad's stock and pre-write assignment backups and
  33 write transactions (`.loom/tied/midi-mvp/unique-assignments.tied/`), the
  RGB memory read and lighting baseline (`.loom/dropped/rgb-feedback/`),
  and four `.log` files (force-added in `af89cb5`, deleted from the tree since,
  still in history).
- Checked contents: only Bob's pad. The captured "text" is the pad's own
  digits and operators (`1`–`9`, `-`, `+`, `*`, `/`, `.`, Enter); no other
  keyboard's typing. Devices named: `G-LRA k16_n3` only (serial `20260101`, a
  placeholder the vendor ships). IORegistry IDs (`DevSrvsID:4295048040`) are
  per-boot. The dumps are settings readouts (key assignments, colours, mode),
  not firmware or flash images.
- Risk: none seen; the ignore comment is about the app's runtime files, and
  these were kept on purpose. Bob's "research public" covers them.
- Options: accept; or reword the `.gitignore` comment (tree only) so a reader
  doesn't see a contradiction. Claude left the comment alone: it describes the
  app's runtime folders correctly.

### F7 — board photos: nothing else visible (info; kept by Bob's word)

Bob, 2026-11-13: "keep the photos". Looked at all six
(`lore:2026-11-13-k16n3-board-photos`; the two in
`.nest/dropped/tengu-glra-osc-extra-photos-20261113/attachments/` are
byte-identical copies of album-2, blobs `4bfb172`, `670e502`):

- EXIF: none. Telegram stripped it; only a JFIF header and an sRGB ICC profile
  (Google, 2016) remain. No GPS, camera model, owner or date.
- Visible beyond the PCB: a wooden tabletop, a white USB-C cable, the pad's
  black case, and (album-2 `source-1.jpg`) an out-of-focus background with
  what looks like striped blue fabric and a white object, and a blurred
  fingertip at the bottom left. Nothing readable or identifying.
- Board text visible (useful, already recorded): `SD014_K009_16Key_ARGB_V2.0`,
  `2026-6-17`, `23IM`, `SDCX` / `SDC32K 952CCU6`, `J1` `GND SCK SDA VDD`.

### F8 — screenshots show Bob's home path (info)

- `.loom/threads/patch-0.1.1/evidence/readback-*.png` (`ed2b147`) show
  `/Users/bob/Library/Application Support/glra-osc/backups/…`. Text history
  also names `/Users/bob/repos/glra-osc` (31×) and `/Users/bob/repos/glra-studio/.venv` (5×).
- Risk: the username `bob` adds nothing to "Bob Jarvis" in every commit.
  Timestamps throughout use +11:00 / "AEDT", which places Bob's timezone.
- Options: accept.

### F9 — GPL: what's there, what was missing (fixed in the tree)

Present as of `48e6c4b`: `LICENSE` (GPL-3.0 text), `pyproject.toml`
`license = "GPL-3.0-only"` with `license-files`, `THIRD_PARTY_NOTICES.md`
attributing `glra_midi/device/` and five app files to glra-studio commit
`33aa281` (Copyright (c) 2026 GLRA Studio contributors),
`glra_midi/device/README.md` with the per-file table, and SPDX plus the
glra-studio copyright line on all 14 files taken from it (checked:
`git grep 'GLRA Studio contributors'`). No vendor JavaScript bundle is copied:
research notes cite vendor function names and opcodes, not code.

Missing, fixed here in `536430a` (tree only, clearly right):

- SPDX line on `test.sh`, `tools/app-capture.sh` and
  `glra_midi/device/__init__.py` (an empty file; glra-studio's own
  `macropad/__init__.py` differs, so this one counts as ours).
- `tomli-w` 1.2.0 (MIT), a runtime dependency in `pyproject.toml`, was absent
  from the notices' dependency table.

Left alone, on purpose:

- `glra_midi/default_profile.toml`, `glra_midi/app/demo_profile.toml`: no
  SPDX line. Users copy these as their own config, and the app drops comments
  on save; a licence line there would mislead more than help.
- Research scripts in `.loom/tied/…` and `.loom/dropped/…` (`probe.py`,
  `capture.py`, `program.py`, `seize.swift`, etc.) have no SPDX line. They are
  tied records; editing them rewrites the record. They import
  `glra_osc.device` rather than copying glra-studio code, so the repo licence
  covers them.
- The primitives' scripts: F5.

### F10 — size (info)

Nothing large. Largest blob 217 KB (a screenshot); 55 image/crash-report
blobs total 4.9 MiB of the 8.7 MiB; pack 3.5 MiB. The many renamed `.loom`
captures share blobs, so they cost nothing extra. No LFS needed.

## Not found

- Credentials of any kind (the only hits were prose: "change token", "sudo
  needs a password", GPL text).
- Other people's personal details. People named: Bob; glra-studio's author by
  GitHub handle (`imolitor`) in links; prior-art repo owners by handle in
  `glean:sdcx-prior-art` and research links. All public.
- Private messages beyond Bob's own words to the agents, which lore and loom
  quote on purpose (briefs, answers, the tour).
- Vendor firmware, flash images, datasheets (the Masses Chip catalogue is
  linked, not copied), copied web pages. ChatGPT reports in lore quote short
  facts with links (`utm_source=chatgpt.com` left in).
- Files other than text, PNG, JPEG and one `.ips` (JSON) in history.

## One thing outside the brief

`inbox` (a tracked symlink to `.nest/in/`) dangles in a fresh clone, because
`.nest/in/` holds no tracked files as of `48e6c4b`. Harmless; noted for
`rename-places` or `first-release`.
