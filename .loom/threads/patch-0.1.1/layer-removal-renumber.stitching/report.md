# layer-removal-renumber: report

Claude (Sonnet 5.5 worker), 2026-11-13. Branch `layer-removal-renumber`, one code commit
(f65c0ea) on top of 0a70043; `main` had nothing newer, so the merge was a no-op.

## What I built

Bob's P1 answer ("p1 yes"): removing a layer now renumbers `layer-set` keys and flags the
ones that pointed at it.

- `glra_midi/profile.py` `remove_layer`: a `layer-set` key pointing above the removed layer
  drops by one, so it still reaches the same content. A key pointing *at* the removed layer
  becomes `LayerSet(layer=NO_LAYER)` (new constant, 0). Keys below it stay. A key already past
  the old count stays past the new count and `validate` still flags it as before.
- `validate`: a `LayerSet(NO_LAYER)` gives one Problem, "`<control>.layer`: the layer it pointed
  at was removed; choose another layer". The app shows it as "Dial 3 push (layer): ..." and it
  blocks Save, like the other Problems. Picking another layer in the inspector clears it.
  A saved file can't carry layer 0 (Save is blocked, and the parser rejects it).
- `glra_midi/app/summary.py`: such a key's tile reads `→ L?` over "removed".
- `docs/config-app.md` 4.7 now describes the rule (the design said "flag past-count keys
  only"; Bob's answer replaces that). CHANGELOG `[Unreleased]` has a Fixed line.
- `glra_midi/app/gui.py`: new capture state `problem-selected`; the `problems` state's
  comment updated (it now shows the "removed" Problem).

## Follow-up after manager review (2026-11-13)

The first commit only handled a top-level `LayerSet`. Now `remove_layer` applies the same rule
(`_follow_removal`) to each kept event inside a per-layer control: above the removed layer drops
by one, at it becomes `LayerSet(NO_LAYER)`. `validate` flags a per-layer one with its layer,
"key.1.layers.2.layer: the layer it pointed at was removed; choose another layer" (the app
shows "Key 1, layer 2 (layer): ..."). Tests: one in `tests/test_profile.py` (renumber and flag,
removing a layer below and at the target) and two in `tests/test_app_summary.py` (tile text, and
the inspector's `describe`, for the global and the per-layer case). `./test.sh`: ruff clean,
597 tests OK.

One fact for the record: a `layer-set` inside a per-layer control can't come from a file or the
editors. `_parse_event` rejects it ("layer keys are global; move it to [key.1]"), `set_event`
refuses it, and `validate` already reports it, with the layer, even before any removal. So this
covers a profile built in code only. A flagged per-layer one therefore gets two Problems (the
"removed" one and the "layer keys are global" one); I left both, as each says something true.

## Choices that could have gone another way

- **How to flag.** `validate` works from the profile alone, and `Edit` has no warnings
  channel, so I used an in-profile sentinel (layer 0) instead of a side list. The cost is a
  value no file may hold; the benefit is that Problems, Save-blocking and undo of the edit
  all work through the existing path.
- **The confirmation text** ("Layer 3 has 5 events. Remove it?") still counts only discarded
  events. It doesn't mention retargeted or flagged keys. Easy to add if Bob wants.
- The inspector's "Go to" box shows empty for a flagged key (no layer chosen), which looks right.

## How I checked

- `./test.sh`: ruff clean, 594 tests OK (as of f65c0ea).
- New tests in `tests/test_profile.py`: renumbering above the removed layer (with round-trip
  and `validate` clean), keys at the removed layer flagged, a key already past the count.
  In `tests/test_app_controller.py`: keys follow after removing a layer below them, a key
  at the removed layer shows in Problems and blocks Save, and choosing another layer clears it.
  The old "past the count" controller test became "removing the last layer flags a key that
  pointed at it", since that case now gets the new message.
- PNGs via `tools/app-capture.sh problems` and `problem-selected` (offscreen, demo data, fakes
  only); I looked at both. Nothing touched a pad.

## Not done / open

- No open questions for Bob. P1's file in `config-app/profile-model.tied/` still says
  "open"; I left tied loom state alone, per the brief.
