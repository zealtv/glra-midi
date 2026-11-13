# config-app-review — a fresh Opus review before the tour

Suggested model: Opus, in a fresh session (not the manager's context).
`../qtable/.glean/findings/strong-model-reviews-at-milestones.md`.

Review-only: everything this thread added since the commit that created it.
Look hardest at: engine state across layer changes and reloads; glide timing
and stuck values; that nothing can write to the pad except the explicit
lighting Apply; profile round-trip and legacy loading; QML holding logic it
shouldn't; the app against `docs/config-app.md` and against Bob's brief
(`lore:2026-11-13-config-app-brief`), line by line.

Save `review.md` here: the commit read, findings ranked with `file:line`. The
manager turns the ones that should be fixed before the tour into small
stitches queued ahead of `config-app-tour` (and anchors the tour on them), and
lists the rest in the tour for Bob.
