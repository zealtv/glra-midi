# layer-removal-renumber — P1 / review finding 3

Bob, 2026-11-13, tour: "p1 yes". Removing a layer renumbers `layer-set` keys
that point above it (so "layer-set 3" follows the old layer 3 to its new
number) and flags keys that pointed at the removed layer in the Problems list.
See `config-app/profile-model.tied/questions.md` P1 and
`config-app/config-app-review.tied/review.md` finding 3 (about 10 lines).
