# fix-reload-cc-state — a profile reload keeps CC values and CC latches

Suggested model: Sonnet. Fix stitch from `config-app-review` finding 1
(`.loom/threads/config-app/config-app-review.tied/review.md`), shaped by the orchestrator on 2026-11-13; fix before the tour.

`runner.py` builds a fresh `Engine` on every reload, so the CC value table
and CC latches reset: after a reload the default profile's right dial jumps
back to its `initial`, `cc-step` keys restart from 0, and a latched
`cc-momentary` at `high` reads as unlatched. Design §3.4 keeps the table
across layer changes and `release_all`; a reload should too.

Do: let the new engine carry the old one's CC table (seed `initial` only for
pairs the old table lacks), and keep CC latch entries whose (control, layer)
still holds an equal latched `cc-momentary` in the new profile. Note latches
still release through `release_all` as now. Tests: turn, reload, the next
turn sends value+1; a latched CC stays latched across a reload that leaves it
unchanged and drops when the control changes. Update `docs/config-app.md` §3
with one sentence on reloads.
