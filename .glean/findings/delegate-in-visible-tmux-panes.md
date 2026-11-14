# Delegate stitches to interactive workers in the tmux panes, following the ai-kit orchestrate process

When dispatching a stitch to a worker agent: run it as an interactive session in a tmux pane Bob can watch, not headless `claude -p`, and follow the `orchestrate` skill in ai-kit.

## Why
Bob, 2026-11-12, starting `rgb-feedback/led-research`: "when you delegate i'd like you to run interactive sessions in the tmux panes so i get some visibility as to what's going (qtable process)". qtable is the peer repo `../qtable` whose manager/worker process is recorded in its glean findings. Until that point this repo's workers ran as `claude -p … | tee log` in the panes, and Bob couldn't follow them.

## How
The source of truth is the `orchestrate` skill, `~/repos/ai-kit/skills/orchestrate/SKILL.md`, from
2026-11-14. It was built from qtable's process, and its `reference/harness-lessons.md` now holds the
general lessons from this repo's `config-app` run too. Each run starts with a run plan Bob approves:
mode, models per role, reviews, usage policy and gates. Send briefs and notes with
`~/repos/ai-kit/tools/send-brief`, and watch panes with `pane-watch`. qtable's glean no longer holds the
general process. As applied here:
- Claim (and queue) the stitch on main when dispatching. The worker doesn't touch loom state.
- Prefer a worktree per worker (`git worktree add ../<repo-folder>-<stitch> -b <stitch> main`, e.g. `../glra-osc-rename-code` before the 2026-11 folder move and `../glra-midi-<stitch>` after it), with the pane started in it (`tmux respawn-pane -k -t <pane> -c <worktree>`). Each worktree needs its own `.venv`. Hardware stitches share one pad: never run two pad-touching workers at once.
- Launch: `claude --model sonnet --allowedTools … -- "Read and follow the brief in <file>"`, so the brief arrives whole. Send mid-run notes with `send-brief`.
- Watch with `pane-watch` (prompts, new `WORKER DONE:`/`WORKER WAITING:` markers, idle or stalled panes). The 2026-11-12/13 runs used a small polling script and a `.worker-done` file instead.
- Usage: the run plan states the floors; they are per run, not standing.

## Unattended queue runs (2026-11-13)
Bob, 2026-11-13: "flesh the loom out so that an opus agent can work through it autonomously, acting as an orchestrator (workflow example in the qtable repo peer to this repo)". The runbook written for that sits at `.loom/tied/config-app/orchestrator.md` (a record of that run; use the ai-kit skill for new ones): the queue bounds the run (now the skill's release mode), new stitches go on the queue, questions for Bob get written down and parked, and the run stops at the tour. No pad writes while unattended.

## The first config-app run (2026-11-13)
Bob: "don't go over 92% of the 5 hourly usage window. pause cleanly if you need to ... ping me on tengu ... commit after each stitch." One Opus manager ran 14 stitches (12 planned, a fix stitch from Bob's design answers, two from the review) with Sonnet workers (Opus for design and review), up to three at once.
- Its general lessons (auto mode with `--allowedTools` raised one approval in the run; write the whole brief before launch; about 1%/min with three Sonnet workers plus the manager, with a pause at 88% ending at 89–90%; `claude-usage` HTTP 429; resuming a paused worker; staging the loom with `git add -A .loom` when tying) moved to ai-kit's `skills/orchestrate/reference/harness-lessons.md` on 2026-11-14.

## Triggers
claude -p, tmux pane, worker pane, delegate, dispatch, orchestrator, orchestrate, run plan, pane-watch, send-brief, unattended, work the queue, qtable process, interactive session

## Associations
- [[brief-is-direction]]
