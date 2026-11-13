# Working notes for agents

glra-midi: host-side middleware that turns the G-LRA K16_N3 macropad into a silent MIDI controller (OSC later), building on the peer repo `../glra-studio`. Named glra-osc until 2026-11-13, when Bob had it renamed (`loom:public-release`); history (lore, tied and dropped stitches, nest receipts) keeps the old name as written then. A development repo; as of 2026-11-13 the MIDI MVP (`midi-mvp`) is tied, `config-app` (a configuration app: layers, events, factory RGB mode, orientation) passed Bob's tour (`.loom/threads/config-app/config-app-tour.tied/tour.md`), and `custom-firmware` and `backlog` (`osc-io`, `midi-feedback`) are parked. The public release (`.loom/threads/public-release/`: rename, release process, audit, first release 0.1.0 on GitHub) sits on the queue; the loom holds its current state.

`CLAUDE.md` is a symlink to this file, so every agent runtime reads the same notes.

## The primitives

This repository's shape is held by the dotdirs at its root. Each is a
self-contained, file-based protocol bundling its own script and data: the
script operates on the directory it lives in, and the file system is the
protocol. Each ships its own `README.md` with the full contract. Read it
before doing anything non-trivial with that primitive.

- 🪺 nestlings — `.nest/` — arrivals: what just came in, waiting to be tended.
- 🔮 glean — `.glean/` — memory: small, current, revisable guidance.
- 🪡 loom — `.loom/` — finite work: goals, stitches, dependencies, queue order.
- 🐉 lore — `.lore/` — the library: complete, dated records, kept whole.
- 🦫 groundhog — `.groundhog/` — what comes around at a set time: recurring and one-shot items. Use it, not a runtime's own cron, for scheduled wake-ups.

In short: the nest holds what just arrived, glean what is true *now*, the loom
what is still to be done, lore what happened, and groundhog what comes next.

### Start here

1. Read `.glean/findings/INDEX.md`, the always-loaded memory surface:
   one line per finding. Open a body only when it is relevant
   (`./.glean/glean.sh fetch <terms>`).
2. Run `./.loom/loom.sh status`. The loom alone owns open work, blockers and
   queue order. Existing stitches don't widen the user's current request.
3. Read `.nest/tend.md` and inspect `.nest/in/` for arrivals waiting to be
   tended. `inbox/` is a symlink to `.nest/in/`.
4. Consult `.lore/INDEX.md` only when complete evidence or history is needed.
   Lore is dark by default.

## Run and test

Python 3.13+ (as of 2026-11-12 Bob's only Python is `/opt/homebrew/bin/python3.14`).

```sh
/opt/homebrew/bin/python3.14 -m venv .venv
.venv/bin/pip install -e '.[dev,gui]'   # gui = PySide6 for the config app; app tests skip without it
./test.sh              # ruff + unittest
.venv/bin/glra-midi --version
```

`glra_midi/device/` holds code vendored from glra-studio (GPL-3.0-only); see its
`README.md` before editing it. This repo is GPL-3.0-only as a result.

## Memory lives in Glean

Glean is this repository's only memory. Don't keep project knowledge in a
runtime's private memory store (for example Claude Code's per-project
`~/.claude/projects/.../memory/`), a `memory/` directory or a handoff note.
Those drift from the repository and travel with one tool on one machine. When
you learn something worth carrying into the next session, it becomes a
finding: search first and revise an existing finding rather than adding a
near-duplicate, run `./.glean/glean.sh index`, and commit it with the work that
earned it. Claude Code's auto memory is switched off here in
`.claude/settings.json` (`autoMemoryEnabled: false`).

## Ownership

One arrival may earn several routes: the source kept in lore, a constraint
distilled into glean, a design change in `docs/`, a stitch on the loom. Those
are different consequences of one thing, not competing copies of it. Name the
results in a nest receipt as `lore:<id>`, `glean:<id>`, `loom:<id>` or
`path:<repo-relative-path>`.
