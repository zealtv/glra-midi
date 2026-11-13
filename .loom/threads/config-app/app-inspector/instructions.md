# app-inspector — edit what a control does

Suggested model: Sonnet. Build to `docs/config-app.md`.

The inspector for the selected control, on the shown layer tab:
- **Presses** (keys, dial pushes): action type = None | Layer select | Event.
  - Layer select: set layer (n) | inc | dec. Choosing it makes the control
    global: it replaces that control's events on every layer (ask before
    discarding any), and the control then shows locked on every tab. Bob: "Any
    press set to change layer becomes global (ie it does not change when the
    layer changes)".
  - Event: layer ("n or global": default the shown tab), MIDI channel, and one
    of Note (momentary | latch; note, velocity), CC momentary (low, high,
    easing time and curve), CC set value, CC inc/dec (step, direction, easing).
- **Dial turns**: None | Relative CC (encoding) | Absolute CC (initial, step),
  with layer and channel.
- On a layer tab, a control inheriting a global event shows it read-only with
  "Override on this layer" and, once overridden, "Use global".
- Fields validate as typed; errors use the profile's own messages. Note numbers
  also show names (C1 = 36, and say which octave convention).
- Every edit goes through the `profile-model` edit helpers and updates the
  tile summary at once; copy/paste of one control's assignment between layers
  or controls if the design includes it.

Tests (offscreen): for each action kind, driving the controller's slots yields
the expected profile; the layer-select rule; override and use-global; invalid
input never reaches the profile. Captures of each inspector state.
