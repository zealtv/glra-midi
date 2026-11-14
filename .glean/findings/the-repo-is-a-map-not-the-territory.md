# The repo is a map built from glimpses, not the territory

Before stating something here as current, say where it came from and when, for example "as of <source>, <date>". The world outside this repo keeps moving, and what the repo holds is only the last glimpse it caught.

## Why

Bob, 2026-10-08: *"things happen in the real world outside of this repo. this repo gets glimpses. one shouldn't confuse the map for the territory."*

A repo learns about its world from conversations, notes, issues, docs and brain-dumps. Decisions, upstream releases, deployments and user feedback happen in between and often never arrive here. So read a figure, date, version or design decision here as "last seen", not "true now".

- **Date and source what you assert.** Prefer "as of <source, date>" to a bare fact, especially for numbers, dates, versions and decisions that other work gets sized against.
- **A gap means the repo didn't capture it, not that it didn't happen.** Don't conclude something is missing, unbuilt or undecided just because the repo has nothing on it. Ask Bob.
- **Check a stale-looking fact before building on it**, most of all a load-bearing one: a dependency's API, a measured limit, an agreed interface.
- **Don't chase certainty.** Record what came in, mark estimates as estimates, and move on. Over-reconciling the map won't make it the territory.

### Write in the spirit of E-Prime

Robert Anton Wilson's notes on E-Prime make good general guidance. (The examples below are illustrations, not facts about this repo.) Avoid the "is" of identity ("the cache is the bottleneck") and the "is" of predication ("the API is stable"). Both state as fixed facts what are really observations made from one viewpoint at one time. Say who observed, decided or measured what, and when:

- Not "the parser is fast enough", but "<who>'s <date> benchmark measured 4 ms per file on <machine>".
- Not "the spec is final", but "Bob signed off on the spec on <date>".
- Not "this is the cause", but "this looks like the cause: the error stops when X changes".

Don't follow it rigidly. Plain "is" is fine for definitions and for things you just verified yourself. The aim is to avoid accidental certainty, not to write in contortions.

This applies a broader principle from Bob's global Claude instructions (`~/.claude/CLAUDE.md`), carried here so that every agent runtime sees it, not only Claude.

## Context

Seeded by ai-kit's `repo-setup` skill (`skills/repo-setup/templates/findings/`). This repo's copy is its own: revise it as the repo learns, and expect it to drift from the seed (Bob, 2026-11-14: "i don't mind if that one drifts. it's designed to"). It started in kite-choir-brains (commit bda42d8, 2026-10-08).

## Triggers

map, territory, glimpse, glimpses, source of truth, ground truth, stale, out of date, moving target, E-Prime, Robert Anton Wilson
