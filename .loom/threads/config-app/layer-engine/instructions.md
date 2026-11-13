# layer-engine — the engine plays a profile: layers, layer keys, per-event channel

Suggested model: Sonnet. Build to `docs/config-app.md`.

Rework `glra_osc/engine.py` (still pure: events in, MIDI bytes out, no clock
yet) to take a profile:
- Active layer state; layer-select presses (`set n`, `inc`, `dec`, wrapping)
  act on press, send no MIDI, and work the same from every layer.
- Resolution on press or turn: a layer action, else the control's global
  event if the control is global, else the active layer's event, else nothing.
  No fall-through and no override (Bob, 2026-11-13: "\"global\" just means it
  is the same on all layers. no fall through mechanism").
- A release goes to the binding the press started with, even if the layer
  changed in between. `release_all()` still clears everything held.
- Latch state per (control, layer) for per-layer controls, one state for a
  global control; switching layers sends nothing.
- Per-event MIDI channel.
- Note momentary and latch; CC set value; CC step and CC momentary **without
  easing** (jump to the target), through one CC value table per (channel, cc)
  that absolute dial turns share. `cc-easing` adds the glides.
- An observer hook for layer changes, so the runner can print them.

Carried from the dropped `banks` sketch: each layer keeps its own latch and
encoder state; switching sends nothing by default.

Tests (fake events only): each kind on global and on a layer; a per-layer
control does nothing on a layer where it has no event; a layer change while a key is held; latch per layer; inc/dec
wrap; shared CC value between a step key, a set key and an absolute dial; the
existing engine tests ported, not deleted.
