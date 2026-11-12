# The brief points a direction; Bob wants a basic working MIDI tool first

When planning or scoping work here, or when tempted to follow the initial brief to the letter: Bob's stated priorities as of 2026-11-12 override it.

## Triggers
- brief
- ChatGPT
- MVP
- BopOS

## Context
What Bob said on 2026-11-12, when the repo got its first loom:
- ChatGPT drafted the brief (`lore:2026-11-12-initial-brief`), and Bob expects
  it makes a lot of assumptions. Take it as a direction, not gospel.
- Basic functionality first. Order: MIDI output, then OSC. The MVP goal on the
  loom is `midi-mvp`; banks, RGB feedback, MIDI feedback and OSC exist as sketch goals.
- glra-studio's tooling doesn't have to be used, but use it where it gives the
  lowest friction (it did: Python + hidapi; see [[glra-studio-reuse]]).
- This is a development repo. Release later via the same process as BopOS
  (as of 2026-11-12, BopOS shipped v1.0.0 as the first commit of a fresh public
  repo). No release stitches yet.
- Bob would rather not grant extra terminal permissions (glra-studio needed
  Input Monitoring). If one turns out to be needed, ask him to add it to
  Ghostty, his current terminal.
- Bob wants the right model for each job: delegate well-specified stitches
  to cheaper models.

## Associations
- [[glra-studio-reuse]]
- [[keyboard-seize-needs-root]]
