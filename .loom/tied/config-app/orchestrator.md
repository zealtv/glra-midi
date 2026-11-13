# Orchestrator runbook for `config-app`

For the Opus session Bob starts to work this thread unattended. Written by
Claude on 2026-11-13 from qtable's process as its glean recorded it that day;
re-read the sources below rather than trusting this summary, since qtable keeps
revising them.

## Read first

1. `AGENTS.md`, `.glean/findings/INDEX.md`, `./.loom/loom.sh status`.
2. `instructions.md` here and `lore:2026-11-13-config-app-brief` (Bob's words).
3. `glean:delegate-in-visible-tmux-panes` (this repo), then qtable's
   `../qtable/.glean/findings/one-worktree-one-cache-one-pane.md`,
   `work-the-queue-as-a-bounded-release.md`,
   `pace-agent-usage-to-the-window-reset.md` and
   `strong-model-reviews-at-milestones.md`.
4. For the shape of an unattended thread: `../qtable/.loom/threads/v3-9-shortcuts/`
   (or `../qtable/.loom/tied/` if it has since been tied).

## Your role

You manage; workers build. You dispatch stitches, answer approval prompts,
review each branch, land it, tie the stitch and keep the loom and queue true.
Do `config-design` yourself or give it to an Opus worker; give build stitches
to Sonnet workers (each stitch names a suggested model). Don't write feature
code in the manager session beyond small landing fixes.

## Bounds

- The queue is the scope. Work it in order; stop when it holds only
  `config-app-tour` (which needs Bob). Don't start `backlog`, `custom-firmware`
  or any new feature, even if `loom.sh next` offers something.
- New stitches are allowed only when they finish what the queue holds: split
  children, fixes from a review, a follow-up a stitch can't close without.
  `loom.sh new <id> config-app`, then queue it in place (`loom.sh before`/`after`)
  and anchor what it blocks. Commit loom changes with the work.
- A question only Bob can answer: write it and the options into the stitch's
  `questions.md`, take the recommended default if the stitch gives one and the
  choice is cheap to reverse, otherwise `loom.sh wait` the stitch and move on.
  List every such question in the tour.
- Device safety: see `instructions.md`. No pad writes in this run.
- Usage: Bob hasn't set floors for this run as of 2026-11-13. Ask him at the
  start if he's there. If he isn't, use these (Claude's suggestion, not Bob's):
  stop dispatching at 90% of the 5-hour window and 80% of the weekly one, read
  with `~/repos/ai-kit/tools/claude-usage`, and have workers wrap at a clean
  commit rather than run dry. Never redeem a banked reset.
- Don't push, tag or publish. Local commits on `main` only.

## The loop

For each ready stitch on the queue (up to three workers at once, one per lane;
only one app-lane worker at a time):

1. **Claim on main**: `./.loom/loom.sh claim <id>`; commit. Workers don't touch
   loom state.
2. **Worktree**: `git worktree add ../glra-osc-<id> -b <id> main`. Create its
   own venv there (`/opt/homebrew/bin/python3.14 -m venv .venv &&
   .venv/bin/pip install -e '.[dev,gui]'`; the `gui` extra exists once
   `app-shell` lands).
3. **Brief**: write `../glra-osc-<id>/BRIEF.md` (untracked; don't commit it)
   from the template below.
4. **Pane**: pick a free pane in the current tmux window (`tmux list-panes`;
   never the manager's own), `tmux respawn-pane -k -t <pane> -c ../glra-osc-<id>`,
   then launch `claude --model <model> --allowedTools … -- "Read and follow the
   brief in BRIEF.md"`. Interactive, never `claude -p`.
5. **Watch** the visible screen (not scrollback) under Monitor: an approval
   prompt ("Do you want to proceed"), the done file, or a screen unchanged for
   about ten minutes. Read each command before approving it. Mid-run notes:
   send the text, then Enter separately, then check the input line is empty.
6. **Review** when `.worker-done` appears: read its report, read the diff
   against main, run `./test.sh` in the worktree, and for app stitches open the
   captured PNGs with Read and compare them with `docs/config-app.md`. Send
   defects back to the same worker as one message. If a second round doesn't
   settle it, shape a fix stitch.
7. **Land**: the branch must already contain main and pass `./test.sh`. Then on
   main: `git merge --ff-only <id>` (or `--no-ff` if main moved; rerun
   `./test.sh` after), `./.loom/loom.sh tie <id>`, commit, `git worktree
   remove ../glra-osc-<id>`, `git branch -d <id>`.
8. **Remember**: anything a later session would need (a Qt quirk, a pad fact, a
   correction from Bob) becomes or revises a glean finding, committed with the work.

## Worker brief template

```
You are a worker on stitch `<id>` of glra-osc, in the worktree ../glra-osc-<id>
on branch <id>. A manager session reviews and lands your work.

Read, in order: AGENTS.md; .glean/findings/INDEX.md (open what bears on this
stitch); .loom/threads/config-app/instructions.md;
.loom/threads/config-app/<id>.stitching/instructions.md (your stitch);
docs/config-app.md (the design; it wins over the stitch where they differ).

Rules:
- Stay in this worktree. Don't touch .loom state, the queue, or other stitches' scope.
- Never write to the pad (see "Device safety"). Tests use fakes.
- ./test.sh must pass before every commit. Commit in small steps on this branch.
- Notes, captures and reports go in your stitch directory.
- If something only Bob can decide blocks you, write it to questions.md in your
  stitch directory, take the stitch's default if it gives one, and say so in
  your report.
- Don't run claude-usage. If told to pause, stop at the next clean commit.

When done: merge main into your branch, rerun ./test.sh, write report.md in
your stitch directory (what you built, what you didn't, how you checked it,
open questions), commit, then `touch .worker-done`.
```

## When the queue is down to the tour

Do `config-app-tour`'s preparation (it says which part), leave it claimed or
waiting as it directs, and message Bob with the `message-bob` skill: what
landed, what didn't, the questions waiting for him. Then stop.

## Starting this run (for Bob)

In the manager pane, from the repo root:

```sh
claude --model opus -- "Read .loom/threads/config-app/orchestrator.md and work the queue as the orchestrator."
```
