# Delegate stitches to interactive workers in the tmux panes, following qtable's process

When dispatching a stitch to a worker agent: run it as an interactive session in a tmux pane Bob can watch, not headless `claude -p`, and follow qtable's established worker process.

## Why
Bob, 2026-11-12, starting `rgb-feedback/led-research`: "when you delegate i'd like you to run interactive sessions in the tmux panes so i get some visibility as to what's going (qtable process)". qtable is the peer repo `../qtable` whose manager/worker process is recorded in its glean findings. Until that point this repo's workers ran as `claude -p … | tee log` in the panes, and Bob couldn't follow them.

## How
The source of truth is qtable's `.glean/findings/one-worktree-one-cache-one-pane.md` (and, for usage, `pace-agent-usage-to-the-window-reset.md`); read it before dispatching. In short, as applied here:
- Claim (and queue) the stitch on main when dispatching. The worker doesn't touch loom state.
- Prefer a worktree per worker (`git worktree add ../<repo-folder>-<stitch> -b <stitch> main`, e.g. `../glra-osc-rename-code` before the 2026-11 folder move and `../glra-midi-<stitch>` after it), with the pane started in it (`tmux respawn-pane -k -t <pane> -c <worktree>`). Each worktree needs its own `.venv`. Hardware stitches share one pad: never run two pad-touching workers at once.
- Launch: `claude --model sonnet --allowedTools … -- "Read and follow the brief in <file>"`. Write the brief to a file and point to it, so the brief arrives whole. For mid-run notes, send the text, then Enter separately, then check the input line is empty.
- Watch the visible screen, not scrollback: approval prompts ("Do you want to proceed"), a done marker (the worker touches a file, since a `WORKER DONE` line in the pasted brief matches itself), and an unchanged screen over ~10 min. In this session (2026-11-12) that watcher was a small polling script on the pane run under Monitor.
- Usage: read `~/repos/ai-kit/tools/claude-usage`; ask Bob for this session's floors. qtable's are per-run, not standing.

## Unattended queue runs (2026-11-13)
Bob, 2026-11-13: "flesh the loom out so that an opus agent can work through it autonomously, acting as an orchestrator (workflow example in the qtable repo peer to this repo)". The runbook written for that sits at `.loom/tied/config-app/orchestrator.md`: the queue bounds the run (qtable's `work-the-queue-as-a-bounded-release.md`), new stitches go on the queue, questions for Bob get written down and parked, and the run stops at the tour. No pad writes while unattended.

## The first config-app run (2026-11-13)
Bob: "don't go over 92% of the 5 hourly usage window. pause cleanly if you need to ... ping me on tengu ... commit after each stitch." One Opus manager ran 14 stitches (12 planned, a fix stitch from Bob's design answers, two from the review) with Sonnet workers (Opus for design and review), up to three at once.
- Workers launched in **auto mode** asked for one approval in the whole run (an `rm -f $D/*.png` on a possibly empty variable; the manager declined it and asked for a literal path). An `--allowedTools` list plus auto mode was enough.
- A brief appended *after* launch can be missed: the worker may already have read it. Write the whole brief before sending the launch command, or send the addition as a note.
- Usage moved about 1%/min with three Sonnet workers plus the manager. Pausing at 88% ended at 89–90%. `claude-usage` sometimes returned HTTP 429; the watcher has to cope with an empty reading.
- A worker paused mid-stitch resumed cleanly after the reset: new session in the same worktree, `rm .worker-done`, and a line in `BRIEF.md` pointing at its `report.md` "Left to do".
- Tying a stitch renames `<id>.stitching` to `<id>.tied`; stage both (`git add -A .loom`), or the deletions get left out of the commit.

## Triggers
claude -p, tmux pane, worker pane, delegate, dispatch, orchestrator, unattended, work the queue, qtable process, interactive session

## Associations
- [[brief-is-direction]]
