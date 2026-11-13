# config-app — a configuration app for the pad: layers, events, RGB mode, orientation

Bob, 2026-11-13 (`lore:2026-11-13-config-app-brief`, read it whole first): "i now
want to look at flesh out a configuration app." Shaped the same day for an
unattended run by an Opus orchestrator: "flesh the loom out so that an opus
agent can work through it autonomously, acting as an orchestrator (workflow
example in the qtable repo peer to this repo)". The runbook for that
orchestrator sits beside this file: `orchestrator.md`.

## What Bob asked for

Keys and encoder presses can each be set to one of:

- **Layer select** ("ie bank"): set layer (n), inc layer, dec layer. "Any press
  set to change layer becomes global (ie it does not change when the layer changes)".
- **Event**, with a layer ("n or global") and a MIDI channel, and one of:
  - "MIDI momentary or latch"
  - "CC momentary (low and high value with easing)"
  - "CC set value"
  - "CC inc or dec with easing"

"The edit page should have a layer selection tab or drop down so layers can be
edited and viewed as a whole." "we also want to select the rgb mode from the
factory firmware. and have an orientation selector." "we can use the
glra-studio as a starting point. references are things like Novation's
configuration software or any other popular MIDI hardware configuration tools."

## Readings of the brief (Claude's, 2026-11-13; Bob corrected 2 and accepted the rest)

Bob, 2026-11-13, on seeing these: "regarding point 2 - \"global\" just means it
is the same on all layers. no fall through mechanism. other than that
everything looks ok." Reading 2 below is his correction. `config-design`
records the details it settles in `docs/config-app.md`.

1. "MIDI momentary or latch" means a **note**, momentary or latched (today's
   `mode = "toggle"`).
2. **Global means the same on all layers; nothing falls through** (Bob). A
   control is either global (one event, identical on every layer) or
   per-layer (an event, or nothing, on each layer separately). It never holds
   both, and no layer overrides a global event.
3. **Encoder turns** stay mappable (today's relative and absolute CC kinds) and
   gain a layer and a channel like presses. The brief names only keys and
   encoder presses; without this, layers couldn't change what a dial does.
4. **Easing** means a glide over a set time (ms) along a curve (linear, ease
   in, ease out, ease in-out); 0 ms jumps.
5. Layers: 1 to 8, default 4, with optional names; inc and dec wrap around.
   Switching layers sends nothing; each layer keeps its own latch state
   (carried over from the dropped `banks` sketch, brief §6).
6. The app edits a **profile file**; `glra-osc run` plays it and reloads it
   when it changes. The app itself doesn't send MIDI in this round.
7. A lighting change reaches the pad only on an explicit **Apply**, because
   every lighting write persists to flash (`glean:k16n3-lighting`).
8. Orientation changes how controls are numbered, labelled and drawn; the
   profile stores assignments by physical position, so turning the pad doesn't
   remap anything.

## Stitches

Order and dependencies (`needs/`); the queue holds the same order.

```
config-design ─ profile-model ─┬─ layer-engine ─ cc-easing ─ runner-profile ─┐
                               ├─ lighting-modes ──────────────┐             │
                               └─ orientation ─ app-shell ─ app-inspector ─ app-device-panel ─┴─ config-app-review ─ config-app-tour
```

Three lanes can run in parallel after `profile-model`: engine
(`layer-engine` → `cc-easing` → `runner-profile`), lighting (`lighting-modes`),
and app (`orientation` → `app-shell` → `app-inspector` → `app-device-panel`).
The app stitches run one at a time: they share `Main.qml` and the controller.

`config-app-tour` needs Bob; an unattended run ends there.

## Not in this thread

- OSC, MIDI input and LED feedback (`loom:backlog`), own firmware (`loom:custom-firmware`).
- Per-key colours, host animations: dropped with `rgb-feedback` on 2026-11-13.
- Editing the pad's stored key assignments (glra-studio does that); the pad
  keeps the 25 unique codes from `loom:unique-assignments`.
- Pressing a pad control to select it in the editor, an in-app "run" switch, a
  menu-bar app, packaging as a `.app`. Note ideas like these in the tour's
  "later" list; don't build them.

## Device safety (every stitch)

Workers and the orchestrator never write to the pad during an unattended run:
no assignment writes, no lighting writes (`06 0b`, `06 14`), no bulk `06 12`.
Reads through the allowlisted vendor reads are fine. Code that writes lighting
gets tested against a fake device; the first real write happens on the tour
with Bob at the pad. No firmware, bootloader or reset commands, ever.
