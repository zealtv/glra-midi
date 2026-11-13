# app-inspector: report

Worker: Claude (Sonnet 5.5), 2026-11-13. Branch `app-inspector`, two commits on top of
`468e005`. `main` had nothing new when I merged it ("Already up to date"). `./test.sh` passes:
494 tests (423 before), ruff clean. I touched no `.loom` state outside this directory, nothing
under `glra_osc/device/`, and the app does no device I/O.

## What I built

- **The inspector edits the selected control on the shown tab** (design 4.5, 4.6):
  - *Presses*: Action = Event | Layer | None. Event shows Applies (This layer | All layers),
    Kind (Note, CC momentary, CC set value, CC inc / dec) and that kind's fields: note (with its
    name beside it, C1 = 36), velocity, latch, CC, low, high, rise ms, fall ms, ease ms, curve,
    value, Inc/Dec plus step size, channel (default or 1..16).
  - *Layer keys*: Set [layer] | Next | Previous. Shows 🔒 on every tab (the tile state was
    already there from `app-shell`).
  - *Dial turns*: the Action row holds the kinds: CC relative (encoding) | CC absolute
    (step, initial) | None, with channel.
  - *"Also on"* lists a per-layer control's other layers; a click jumps to that tab.
  - *Global tab*: a per-layer control shows "Different on each layer", the layers it uses and
    **Make global…**; its fields stay hidden (pick a layer tab).
- **`glra_osc/app/inspector.py`** (pure, no Qt): `describe` builds the dict the QML reads,
  `apply_field` and `default_event` build the event a typed value produces, `discard_text`
  words the questions.
- **Controller slots** (`controller.py`): `setAction`, `setKind`, `setField`, `setApplies`,
  `setLayerKey`. Each calls a `profile.py` edit helper (`set_event`, `clear_event`,
  `make_global`, `make_per_layer`, `set_layer_key`) and `_edit`, so tiles and the dirty flag
  update at once.
- **Three small public helpers in `profile.py`** (`event_field_specs`, `event_fields`,
  `event_from_fields`) that read the parser's own spec table. A typed value therefore passes
  through the same checks as a file and says the file's words
  (`expected an integer 0..127, got 300`; I drop the key path, since the label is the path).
- **QML**: `Inspector.qml` rewritten (scrolls when the fields outgrow the panel), plus
  `AppField.qml`, `AppChoice.qml` and `Segmented.qml`. The panel went from 280 to 330 px wide.
- **Capture states** in `gui.py`: `inspector-note`, `-note-global`, `-cc-momentary`, `-cc-set`,
  `-cc-step`, `-layer-key`, `-turn-relative`, `-turn-absolute`, `-empty-key`, `-global-tab`,
  `-invalid`, `-make-global`.

## The rules as built

- **Invalid input never reaches the profile.** A rejected entry stays in its field with a red
  border and the profile's message; the profile keeps its last valid value. The draft lasts
  until the selection, tab or kind changes.
- **Event → layer key** (and any control that holds events) asks first, naming the layers
  ("Key 2 has its own events on layers 1 and 2. Make it a layer key and discard them?").
  Choosing a different layer key, or a layer key on an empty control, doesn't ask.
- **Per-layer → global** asks when other layers hold a *different* event ("Key 2 has its own
  events on layer 2. Make layer 1's event apply to all layers and discard those?"). From the
  Global tab the lowest layer's event is kept.
- **Global → per-layer** copies the event to every layer, no question. After that an edit
  changes only the shown layer.
- **Layer key → event** becomes a per-layer event on the shown layer (global on the Global
  tab). **None** clears one layer of a per-layer control, but the whole control when it is
  global or a layer key (design 4.6).
- Editing a global event from any tab changes it for every layer.

## How I checked

- `tests/test_app_inspector_model.py` (21, pure): defaults for every kind, `apply_field`
  (ranges, empties, `default` channel, the Inc/Dec + size halves of `step`, the same message the
  parser gives for a file), `describe` for each control shape.
- `tests/test_app_inspector.py` (39, offscreen, controller slots): each action kind yields the
  expected profile; the layer-key rule with accept and decline; global ↔ per-layer both ways;
  invalid text of several shapes never changes the profile and shows the profile's message;
  the saved file reloads to the same profile; a cross-control `initial` clash lands in the
  problems list and blocks Save.
- `tests/test_app_qml.py` (+7): zero QML warnings across every kind, tab and error state; real
  typing into the note field (valid and invalid); the Action, Applies and layer-key buttons;
  the Latch switch; Make global opens the confirm dialog; "Also on" jumps to the layer.
- `tests/test_profile.py` (+3) for the new helpers.
- I looked at every capture in `captures/` myself. **Not checked:** a real on-screen launch
  (everything ran offscreen), dark mode for the new fields beyond the shared palette, and a
  real mouse in the drop-downs (the tests set values through the controller, and I never opened
  a combo's popup).

## What I didn't build

No copy/paste of events between controls or layers, no undo (Revert covers a big mistake): both
belong on the tour's "later" list, as the stitch said. No per-direction curve for
`cc-momentary` (design 2.3 keeps one `curve`).

## Readings and choices where the design or stitch left room

1. **Fields apply as you type.** Typing `300` into Note passes through `3` and `30`, both
   valid, so the profile briefly takes note 3, then 30, and ends on 30 with the error showing.
   The alternative (apply on Enter or focus loss) would leave the tile stale while typing, which
   "validate as typed" and "updates the tile summary at once" argue against. Easy to flip in
   `AppField.qml` (`onEditingFinished` in place of `onTextEdited`).
2. **Applies shows only once the control has an event.** To make a new control global, create
   the event on the Global tab, or flip Applies afterwards.
3. **Action → Layer starts as "Next"** (`layer-inc`), which needs no layer number; the Set
   choice then offers the layer drop-down.
4. **Dial-turn kinds sit in the Action row**, as the design's wireframe has them, rather than
   under a Kind drop-down.
5. **The old summary lines** under the title (from `app-shell`) are gone; the fields show the
   same facts.
6. **Field messages drop the key path** (`expected an integer 0..127, got 300`); the problems
   list above the pad still shows the full, displayed-label form.
7. I added the three `profile.py` helpers; that file belongs to `profile-model`, which is tied.
   They only read its spec table.

## Open questions

None that block; `questions.md` not written. For the tour: item 1 above, and whether the
inspector at 330 px feels cramped for CC momentary (twelve rows; it scrolls).
