# The configuration app: design

Written by Claude (Opus worker on `loom:config-design`), 2026-11-13. Every
later `config-app` stitch builds to this file; where a stitch's
`instructions.md` disagrees, this file wins.

Sources: Bob's brief (`lore:2026-11-13-config-app-brief`), the eight readings
in `.loom/threads/config-app/instructions.md` (Bob accepted them on
2026-11-13 and corrected reading 2: "\"global\" just means it is the same on
all layers. no fall through mechanism"), `glean:k16n3-lighting`,
`glean:k16n3-hid-interfaces` and `glra_osc/device/layout.json` as of
2026-11-13, and the references in
`.loom/threads/config-app/config-design.stitching/references.md`.

Unless a line names Bob, each decision below is **Claude's default**. Defaults
that Bob might well want differently are listed in that stitch's
`questions.md`; the tour puts them in front of him.

Contents: 1 references · 2 profile format · 3 engine · 4 app · 5 lighting ·
6 orientation · 7 open questions.

---

## 1. What the references gave us

Five configurators read on 2026-11-13 (Novation Components, Akai MPK mini
Editor, Arturia MIDI Control Center, Intech Grid Editor, Elgato Stream Deck)
share one layout, and the app takes it:

- **The pad drawn in the middle, click to select.** All five do this; it needs
  no learning.
- **A short summary on each tile, the fields in one inspector.** Novation and
  Arturia do this; Akai's fields-in-the-tile gets cramped at 16 tiles.
- **Layer tabs above the pad** (Intech pages, Stream Deck pages): one click
  shows a whole layer, as Bob asked ("layers can be edited and viewed as a
  whole").
- **Layer keys appear on every layer** (Stream Deck's page keys), matching
  Bob's "any press set to change layer becomes global".
- **Device writes only on an explicit button** (Novation "Send to", Akai
  "Send"); Arturia's live sync is what we avoid, since every lighting write
  persists to flash.

---

## 2. Profile format

**Decision:** a TOML file, read with `tomllib`, written with `tomli-w` (new
dependency, pinned like the others), at
`~/Library/Application Support/glra-osc/profile.toml`. *Why:* the repo already
uses TOML for mappings, Bob can hand-edit it, and `tomli-w` writes the subset
we need with stable output.

### 2.1 Top level

| Key / table | Meaning | Default |
| --- | --- | --- |
| `version = 1` | Marks a profile. A file without it loads as a **legacy mapping** (2.6). | required |
| `[midi] port` | Virtual MIDI port name. | `"GLRA K16"` |
| `[midi] channel` | Default channel 1..16 for events that don't name one. | `1` |
| `[pad] orientation` | `"dials-top"` \| `"dials-right"` \| `"dials-bottom"` \| `"dials-left"` (section 6). | `"dials-top"` |
| `[layers] count` | 1..8. | `4` |
| `[layers] names` | List of up to `count` strings; `""` or missing means unnamed. | `[]` |
| `[lighting]` | Optional factory RGB mode (section 5). Absent: the app leaves the pad's lighting alone. | absent |
| `[key.N]`, `[enc.N.push]`, `[enc.N.turn]` | One table per control that does something. Missing: does nothing. | — |

Control names stay today's **physical** names (`key.1`..`key.16`,
`enc.1`..`enc.3`, as `layout.json` numbers them with the dials along the top).
The app shows displayed numbers for the chosen orientation; the file never
changes when the orientation does (reading 8). *Why:* a profile written for one
way of holding the pad keeps working when Bob turns it.

### 2.2 A control: global, per-layer or a layer key

Each control table takes exactly **one** of three shapes. Mixing them is an
error naming the control (Bob, 2026-11-13: global and per-layer exclude each
other, no fall-through).

1. **Global event**: `kind` and its fields directly in the control's table.
   The same event on every layer.
2. **Per-layer events**: only sub-tables `layers.<n>` (n = 1..count), each with
   `kind` and fields. Layers without one do nothing.
3. **Layer key** (presses only): `kind = "layer-set" | "layer-inc" |
   "layer-dec"` directly in the table. Global by construction; a layer key in a
   `layers.<n>` table is an error ("layer keys are global; move it to
   [key.4]").

A control table that holds neither `kind` nor `layers` is an error (an empty
table usually means a typo); leave the control out instead.

### 2.3 Press kinds (keys and dial pushes)

Every event takes an optional `channel` (1..16; default `[midi] channel`).

| `kind` | Fields (default) | Bob's words |
| --- | --- | --- |
| `note` | `note` 0..127, `velocity` 1..127 (127), `mode` = `"momentary"` \| `"latch"` ("momentary") | "MIDI momentary or latch" |
| `cc-momentary` | `cc`, `low` (0), `high` (127), `ease-ms` 0..10000 (0), `curve` ("linear"), `mode` = `"momentary"` \| `"latch"` ("momentary") | "CC momentary (low and high value with easing)" |
| `cc-set` | `cc`, `value` 0..127 | "CC set value" |
| `cc-step` | `cc`, `step` −127..127, not 0, `ease-ms` (0), `curve` ("linear") | "CC inc or dec with easing" |
| `layer-set` | `layer` 1..count | "set layer (n)" |
| `layer-inc` | — | "inc layer" |
| `layer-dec` | — | "dec layer" |

`curve` = `"linear"` \| `"ease-in"` \| `"ease-out"` \| `"ease-in-out"`.

- `cc-momentary` with `mode = "latch"` exists so that today's toggled CC keys
  (`mode = "toggle"` on a `cc` binding) load without loss; the app offers it
  as a "Latch" switch, as for notes. (Question Q1.)
- `cc-step` direction lives in the sign of `step`; the app shows it as
  "Inc / Dec" plus a size. *Why:* one field, no impossible combinations.
- One `ease-ms` and `curve` serve both directions of `cc-momentary`.
  (Question Q2.)

### 2.4 Turn kinds (`enc.N.turn`)

| `kind` | Fields (default) |
| --- | --- |
| `cc-relative` | `cc`, `encoding` = `"twos-complement"` \| `"binary-offset"` \| `"signed-bit"` ("twos-complement"), `channel` |
| `cc-absolute` | `cc`, `step` 1..127 (1), `initial` 0..127 (optional), `channel` |

Turns take the global or per-layer shape like presses (reading 3), never a
layer key. Turn tables take no easing.

`initial` seeds the shared CC value for that (channel, cc) (3.4). Two
bindings that give different `initial`s for the same (channel, cc) are an
error naming both.

### 2.5 A full example

```toml
# glra-osc profile. Control names are physical (dials along the top,
# key 1 top-left); the app shows them in your chosen orientation.
version = 1

[midi]
port = "GLRA K16"
channel = 1

[pad]
orientation = "dials-top"

[layers]
count = 4
names = ["Drums", "Synth", "", "Mixer"]

[lighting]
mode = 2            # Breathing
brightness = 4      # 0..4
speed = 2           # 0..4
color = [0, 255, 255]   # fixed hue h, s, v (0..255); leave out for the mode's own colours

# A global note: the same on every layer.
[key.1]
kind = "note"
note = 36
velocity = 110

# Per-layer: a latched note on layer 1, a CC glide on layer 2, nothing on 3 and 4.
[key.2.layers.1]
kind = "note"
note = 37
mode = "latch"

[key.2.layers.2]
kind = "cc-momentary"
cc = 20
low = 10
high = 120
ease-ms = 250
curve = "ease-out"
channel = 2

# CC set and CC step.
[key.3]
kind = "cc-set"
cc = 21
value = 64

[key.4.layers.1]
kind = "cc-step"
cc = 21
step = 8
ease-ms = 120
curve = "ease-in-out"

[key.8.layers.1]
kind = "cc-step"
cc = 21
step = -8
ease-ms = 120
curve = "ease-in-out"

# Layer keys: global by construction.
[key.13]
kind = "layer-set"
layer = 1

[enc.1.push]
kind = "layer-dec"

[enc.3.push]
kind = "layer-inc"

# Dial turns: global relative, per-layer absolute sharing cc 21 with keys 3, 4, 8.
[enc.1.turn]
kind = "cc-relative"
cc = 16

[enc.2.turn.layers.1]
kind = "cc-absolute"
cc = 21
step = 2
initial = 64

[enc.2.turn.layers.2]
kind = "cc-relative"
cc = 17
encoding = "binary-offset"
```

### 2.6 Legacy mapping files

A file without `version` goes through today's `mapping.py` parser unchanged and
converts to a one-layer profile with every control global:

| Mapping | Profile |
| --- | --- |
| `[global] port, channel` | `[midi] port, channel` |
| `note … mode = "momentary"\|"toggle"` | `note … mode = "momentary"\|"latch"` |
| `cc, on, off, mode` | `cc-momentary`, `high = on`, `low = off`, `mode` (toggle → latch), `ease-ms = 0` |
| `type = "relative"` | `cc-relative` |
| `type = "absolute", initial, step` | `cc-absolute`, `initial`, `step` |

**Decision:** `mapping.py` stays as the legacy reader only (and the adapter
for `Engine` until `layer-engine` lands); new code reads `profile.py`.
`default_mapping.toml` stays shipped for `--config` and tests. *Why:* the
legacy path then stays tested by the tests it already has.

Saving a legacy file from the app writes a profile (with `version = 1`), to
the user's profile path unless Bob chose Save As; the app says so in the
status line ("Opened an old mapping file; it will be saved as a profile").

### 2.7 The default profile

`glra_osc/default_profile.toml`, comments documenting the format (like
`default_mapping.toml` does). Content (Claude's default, Q3):

- 4 layers, unnamed.
- Keys: per-layer notes, `36 + 16 × (layer − 1) + (key − 1)`, so layer 1 plays
  36–51 as today, layer 2 52–67, layer 3 68–83, layer 4 84–99.
- Dial pushes: `enc.1.push` = layer-dec, `enc.2.push` = layer-set 1,
  `enc.3.push` = layer-inc.
- Dial turns: global `cc-relative` 16, 17, 18 as today.
- No `[lighting]`.

### 2.8 Writing

`dump_profile` writes keys in a fixed order (top level, `[midi]`, `[pad]`,
`[layers]`, `[lighting]`, then controls key.1..16, enc.1..3, push before
turn, layers ascending) and leaves out fields equal to their defaults except
`kind` and the number fields that kind requires. It writes a one-line header
comment pointing at the default profile for the format. Comments in a
hand-edited file don't survive an app save (tomli-w writes no comments); the
app warns once per file when the file it opened contained comments.

Saving writes to a temporary file in the same directory and renames it over
the old one, so `glra-osc run` never reads half a file.

### 2.9 Errors

As in `mapping.py`: `ProfileError` messages start with the key path, for
example `key.4.layers.2.cc: must be 0..127, got 300` or
`key.13: a layer key can't also have per-layer events`. Unknown keys are
errors. `layer-set` to a layer above `count` is an error at the key
(`enc.2.push.layer: layer 6 doesn't exist (count = 4)`).

---

## 3. Engine semantics

Still pure (events in, MIDI bytes out). The clock comes in through the event's
`t` and `tick(now)`; nothing sleeps.

### 3.1 Resolution

On a press or turn of control C, with active layer L:

1. C holds a layer key → change layer (3.2); send nothing.
2. C holds a global event → that event.
3. C holds per-layer events → the event for L, if any.
4. Otherwise nothing.

No fall-through between 2 and 3: a control is one or the other (Bob,
2026-11-13).

### 3.2 Layers

- The active layer starts at 1 when the engine starts.
- `layer-set n` sets it; `layer-inc` / `layer-dec` add or subtract one,
  wrapping (count → 1, 1 → count). Acts on press; the release does nothing.
- A layer change sends no MIDI. An observer hook (`on_layer(old, new)`) lets the
  runner print it.
- With `count = 1`, inc and dec do nothing (still valid).

### 3.3 What a layer change does to things in flight

**A release goes to the binding its press started.** The engine records, per
held control, the (control, layer-or-global) binding the press resolved to;
the release uses that, whatever the active layer is now. So:

- A held note stays on until its key comes up, then sends its own Note Off.
- A held `cc-momentary` glides (or jumps) back to its own `low` on release.
- Running glides keep running to their targets; a layer change doesn't touch
  them.
- Pressing a layer key while other keys are held changes the layer and leaves
  the held keys alone.

*Why:* this rules out stuck notes, and nothing surprising happens to sound
already playing.

### 3.4 State

- **Latch state per (control, layer)** for per-layer controls; one per control
  for global ones. Leaving a layer leaves its latched notes sounding; going
  back and pressing again turns them off (carried from the dropped `banks`
  sketch).
- **One CC value per (channel, cc)**, shared by `cc-set`, `cc-step`,
  `cc-momentary` and `cc-absolute`. It starts at the `initial` some absolute
  dial gives it (2.4), else 0. Relative dials send deltas and neither read nor
  change it.
- The value table survives layer changes; `release_all` doesn't reset it.

### 3.5 What each kind sends

| Kind | Press | Release |
| --- | --- | --- |
| `note` momentary | Note On (velocity) | Note Off |
| `note` latch | toggles: Note On or Note Off | nothing |
| `cc-momentary` momentary | glide to `high` | glide to `low` |
| `cc-momentary` latch | toggles the target between `high` and `low`, glides | nothing |
| `cc-set` | cancels any glide; sends `value` (always, even if unchanged) | nothing |
| `cc-step` | target = (current target, or the value if none) + `step`, clamped 0..127; glide there | nothing |
| `cc-absolute` (turn) | cancels any glide; value ± `step`, clamped; sends only on change | — |
| `cc-relative` (turn) | one delta per detent, as today | — |

`cc-set` always sends so a "send 64" key works as a reset even when the host
lost track. `cc-step` at a clamp with no glide running sends nothing.

Two controls on the same note: each press sends its Note On, each release its
Note Off, as today (no reference counting).

### 3.6 Glides

- A glide on (channel, cc) holds: start value, target, start time `t0`,
  duration `d` (the event's `ease-ms`), curve.
- Value at time t: `start + (target − start) × f(min(1, (t − t0)/d))`, rounded
  to the nearest integer, sent only when that integer differs from the last
  value sent on that (channel, cc). It ends exactly on the target at
  `t ≥ t0 + d`.
- Curves, with p in 0..1: linear `p`; ease-in `p²`; ease-out `1 − (1 − p)²`;
  ease-in-out `2p²` for p < ½, else `1 − 2(1 − p)²`. (Quadratic; Q4.)
- **The duration is the full `ease-ms` for each new target**, not scaled by the
  distance. *Why:* a step key then always takes the time it shows.
- **A second press during a glide retargets** it: the new glide starts from the
  current sent value at the event's `t`, aims at the new target, and takes the
  full time again. For `cc-step` the new target builds on the old target, so
  three quick +8 presses from 0 end at 24.
- **One glide per (channel, cc).** Any later event on that pair (another
  glide, a `cc-set`, an absolute turn) replaces it.
- `ease-ms = 0` jumps: the message goes out from `handle` itself.
- `handle(event)` with `ease-ms > 0` starts the glide and returns nothing (the
  value at progress 0 equals the start); `tick(now)` returns what is due;
  `next_due()` returns the time of the next tick, or `None` when nothing
  glides.

**Tick rate:** 100 Hz (every 10 ms) while any glide runs; idle otherwise.
At most one message per (channel, cc) per tick. *Why:* 10 ms steps sound
smooth for CC and stay well under the bandwidth of a virtual port.

### 3.7 `release_all()`

Called on exit, on profile reload and when the pad goes away:

- Note Off for every held note and every latched note; latches reset.
- Every held `cc-momentary` jumps to its `low`.
- Every other running glide jumps to its target.
- Latched `cc-momentary` keeps its value (as today's toggled CC does).

*Why:* afterwards nothing sounds and every CC sits on a value the profile
named, not somewhere mid-glide.

---

## 4. The app

### 4.1 Stack and start

PySide6 6.10.2 + Qt Quick, as in `../glra-studio/macropad/` on 2026-11-13
(`gui.py`, `qml/`, GPL-3.0-only like this repo; record what's taken in
`THIRD_PARTY_NOTICES.md`). A `gui` extra (`PySide6==6.10.2`), entry points
`glra-osc-config` and `glra-osc config`. The CLI imports without PySide6.

The model lives in Python: a `Controller(QObject)` holds a `profile.Profile`
and exposes properties and slots. QML draws and calls slots; it holds no
profile logic and no summary text.

### 4.2 Module layout

```
glra_osc/app/
  __init__.py
  __main__.py      # python -m glra_osc.app
  gui.py           # QGuiApplication, QML engine, --demo, --capture
  controller.py    # Controller(QObject): profile, tab, selection, dirty, file ops
  summary.py       # pure: tile text for every kind (tested without Qt)
  device.py        # pad reads and the one lighting Apply, in a worker thread; FakePad
  qml/
    Main.qml        # window: toolbar, layer tabs, pad view, inspector, device panel
    PadView.qml     # 16 keys + 3 dials placed by orientation.py
    KeyTile.qml     # one key or dial-push tile
    DialTile.qml    # one dial: push tile + turn tile
    LayerTabs.qml
    Inspector.qml
    DevicePanel.qml
```

### 4.3 Window

One window, about 1000 × 640, resizable. Toolbar on top, layer tabs above the
pad, inspector on the right, device panel as a collapsible strip at the
bottom.

```
┌─ glra-osc config — profile.toml • ─────────────────────────────────────────┐
│ [Open…] [Save] [Save As…] [Revert]                    Pad: connected (103) │
├────────────────────────────────────────────────────────────────────────────┤
│ ( Global ) [ 1 Drums ] ( 2 Synth ) ( 3 ) ( 4 Mixer ) [+]         [Rename…] │
├───────────────────────────────────────────────┬────────────────────────────┤
│   ╭─ D1 ──────╮ ╭─ D2 ──────╮ ╭─ D3 ──────╮  │ INSPECTOR                  │
│   │ push ◀ L−1🔒│ │ push → L1🔒│ │ push L+1 ▶🔒│  │  (section 4.5)             │
│   │ turn CC16 G│ │ turn CC21 abs│ │ turn CC18 G│  │                            │
│   ╰───────────╯ ╰───────────╯ ╰───────────╯  │                            │
│  ┌────────┐┌────────┐┌────────┐┌────────┐    │                            │
│  │1     G ││2       ││3     G ││4       │    │                            │
│  │Note C1 ││Note C#1││CC21=64 ││CC21 +8 │    │                            │
│  │vel 110 ││latch   ││        ││120 ms  │    │                            │
│  └────────┘└────────┘└────────┘└────────┘    │                            │
│  ┌────────┐┌────────┐┌────────┐┌────────┐    │                            │
│  │5       ││6       ││7       ││8       │    │                            │
│  │   —    ││   —    ││   —    ││CC21 −8 │    │                            │
│  └────────┘└────────┘└────────┘└────────┘    │                            │
│  … rows 3 and 4 …  (13: → L1 🔒)              │                            │
├───────────────────────────────────────────────┴────────────────────────────┤
│ ▸ Device: RGB Breathing · orientation dials-top · port "GLRA K16" ch 1      │
└────────────────────────────────────────────────────────────────────────────┘
```

`•` after the file name marks unsaved changes. The selected control gets a
thick accent border. Dials draw as a round push tile with the turn summary
under it; push and turn select separately.

### 4.4 Tiles

Tile states look different (colour and badge, not colour alone):

| State | Look |
| --- | --- |
| Empty on this tab | muted `—` |
| Per-layer event on this layer | plain tile |
| Global event | tile with a **G** badge; same text on every tab |
| Layer key | accent tile with a 🔒 badge; same on every tab |
| On the Global tab, a per-layer control | dimmed, text "per layer", plus how many layers use it ("3 of 4") |

Summary text (`summary.py`; two short lines; the channel shows only when it
differs from `[midi] channel`, as `ch 10`):

| Kind | Line 1 | Line 2 |
| --- | --- | --- |
| note momentary | `Note C1` (`36` when names are off) | `vel 110` |
| note latch | `Note C#1` | `latch · vel 127` |
| cc-momentary | `CC20 10↔120` | `250 ms ease-out` (or `latch`, or blank at 0 ms) |
| cc-set | `CC21 = 64` | — |
| cc-step | `CC21 +8` / `CC21 −8` | `120 ms` (blank at 0 ms) |
| layer-set | `→ L1` | the layer name if any |
| layer-inc / layer-dec | `L+1 ▶` / `◀ L−1` | `wraps` |
| cc-relative | `CC16 rel` | encoding, short: `2's`, `offset`, `sign` |
| cc-absolute | `CC21 abs` | `step 2` |

Note names: **C1 = 36**, so middle C (60) reads C3, the convention Ableton
Live and Yamaha use. *Why:* the brief's references and Bob's DAW tools mostly
use it; the inspector shows the number beside the name, so nothing hides.

### 4.5 Inspector

The right-hand panel edits the selected control on the shown tab. Every field
change calls one controller slot, which calls a `profile.py` edit helper and
replaces the profile; tiles update at once.

**Nothing selected**

```
│ INSPECTOR                    │
│ Click a key or dial to edit. │
│                              │
│ Layer 1 "Drums": 9 of 19     │
│ controls do something here.  │
```

**A press (key or dial push)**

```
│ KEY 2 · layer 1 "Drums"           │
│ Action   (•) Event  ( ) Layer  ( ) None │
│ Applies  (•) This layer  ( ) All layers (global) │
│ Kind     [ Note ▾ ]                │
│ Note     [ 37 ] C#1                │
│ Velocity [ 127 ]                   │
│ Latch    [ ]                       │
│ Channel  [ default (1) ▾ ]         │
│                                    │
│ Also on: L2 CC20 10↔120 · L3 — · L4 — │
```

- Kind `CC momentary`: Low, High, Ease ms, Curve, Latch.
- Kind `CC set`: CC, Value.
- Kind `CC inc/dec`: CC, (•) Inc ( ) Dec, Step size 1..127, Ease ms, Curve.
- "Also on" lists the control's other layers (per-layer controls only); a
  click jumps to that tab.

**A layer key**

```
│ DIAL 3 PUSH · 🔒 on every layer    │
│ Action   ( ) Event  (•) Layer  ( ) None │
│ Layer    ( ) Set [ 1 ▾ ]  (•) Next  ( ) Previous │
│ Layer keys work the same on every  │
│ layer, so they can't hold events.  │
```

**A dial turn**

```
│ DIAL 2 TURN · layer 1 "Drums"     │
│ Action   (•) CC relative ( ) CC absolute ( ) None │
│ Applies  (•) This layer  ( ) All layers (global) │
│ CC       [ 17 ]                    │
│ Encoding [ two's complement ▾ ]    │
│ Channel  [ default (1) ▾ ]         │
```

**On the Global tab**, "Applies" shows `All layers` for global controls. For a
per-layer control it shows "Different on each layer" with a list of its
layers and a [Make global…] button; its event fields are hidden (pick a layer
tab to edit one layer).

### 4.6 Switching between global, per-layer and layer key

Bob, 2026-11-13: global and per-layer exclude each other; "any press set to
change layer becomes global". The rules (Claude's defaults where not Bob's):

| From → to | What happens | Asks first? |
| --- | --- | --- |
| per-layer → global (from layer tab n) | The event on layer n becomes the global event; other layers' events go. | Yes, if another layer holds a *different* event: "Key 2 has its own events on layers 2 and 3. Make layer 1's event apply to all layers and discard those?" |
| per-layer → global (from the Global tab) | The lowest-numbered layer's event becomes global. | Same rule. |
| global → per-layer | **The event is copied to every layer**, so nothing changes in play until Bob edits a layer. | No (nothing is lost). |
| event → layer key | All the control's events go; it shows 🔒 on every tab. | Yes, if it held any event. |
| layer key → event | Becomes a per-layer event on the shown layer (global on the Global tab), empty elsewhere. | No. |
| anything → None | Clears the control on the shown layer only for a per-layer control; everywhere for a global one or a layer key. | No (Revert undoes). |

*Why the copy on global → per-layer:* it loses nothing and needs no question;
the stitch's earlier default ("stays on the shown layer only") emptied the
other layers silently. (Q5.)

### 4.7 Layer tabs

- Tabs: `Global`, then `1 Name`..`n Name`, then `[+]`.
- `[+]` adds a layer (up to 8), empty. Right-click (or the Rename… button) on a
  tab: Rename, Remove. Remove asks when the layer holds any event ("Layer 3
  has 5 events. Remove it?"), drops its events, and renumbers the layers
  above it down by one; `layer-set` keys pointing above the new count are
  flagged (below) rather than silently changed.
- At least one layer always remains.
- The app's shown tab doesn't change the engine's active layer; the app plays
  nothing (reading 6).

### 4.8 Files: dirty, save, revert

- On start the app opens the user's profile path; if it's missing, it opens the
  default profile marked dirty, and the first Save creates the user's file
  (and its directory).
- Open… reads any profile or legacy mapping (2.6). Save writes atomically
  (2.8). Save As… picks a path; the window then edits that file.
- Revert re-reads the file from disk after a confirm when dirty.
- Quit, Open… and Revert ask "Save changes to profile.toml?" (Save / Don't save /
  Cancel) when dirty.
- No undo stack this round (Revert covers the big mistake); note it in the
  tour's "later" list.
- If the file changes on disk while open and the app has no unsaved edits, it
  reloads; with unsaved edits it shows "profile.toml changed on disk" with
  [Reload] [Keep mine].

### 4.9 Validation

Fields can't hold out-of-range values (spin boxes with limits, pickers for
choices). Problems that span controls show in a list above the inspector and
block Save, each naming the control and what to do:

- `Key 13: goes to layer 6, but there are 4 layers.` [Select]
- `CC 21 on channel 1: dial 2 starts it at 64, dial 3 at 0. Use one start value.`

The messages come from `ProfileError` and the profile's validator, so the
file and the app say the same thing.

### 4.10 Device panel

Collapsed it shows one line (see 4.3). Expanded:

```
├ Device ────────────────────────────────────────────────────────────────────┤
│ Orientation (•) Dials top ( ) Dials right ( ) Dials bottom ( ) Dials left  │
│ MIDI port [ GLRA K16        ]   Default channel [ 1 ▾ ]                   │
│ Lighting  [ Breathing ▾ ] Brightness [ 4 ▾ ] Speed [ 2 ▾ ]                │
│           [x] One colour  Hue ▭▭▭▭▭▭▭▭  Sat ▭▭▭▭  Value ▭▭▭▭              │
│           Pad now: Rainbow flow (mode 4) · brightness 4 · speed 3          │
│           [ Apply to pad ]  Each Apply is saved in the pad's memory.       │
│           Last: "Applied and read back." / "Already set." / error text     │
```

- Orientation redraws and renumbers the pad view at once (section 6).
- The lighting fields edit the profile's `[lighting]` (section 5); only
  [Apply to pad] touches the pad.
- "Pad now" comes from a read (`06 0a`). With no pad: "Pad: not found", the
  Apply button is disabled, and everything else works.

### 4.11 Testing without a display

- `QT_QPA_PLATFORM=offscreen` for every app test. Tests skip, with a reason,
  when PySide6 isn't installed, so `./test.sh` still passes in a venv without
  the `gui` extra.
- A load test: the QML loads with zero warnings (collect them with
  `qInstallMessageHandler`, fail on any).
- Controller tests drive slots and check the profile, the tile summaries, and
  dirty state. `summary.py` gets plain unit tests.
- Device code takes a pad object; tests pass `FakePad`, which records calls,
  and `--demo` runs the app on `FakePad` too.

### 4.12 Screenshots for review

`tools/app-capture.sh <state> <out.png>` runs
`python -m glra_osc.app --demo --capture <state> --out <out.png>` offscreen:
the app loads a fixture profile, drives the controller into the named state,
waits for a frame, saves `QQuickWindow.grabWindow()` and exits (glra-studio's
`gui.py` captures the same way). States are named after the wireframes above
(`empty`, `layer-tab`, `global-tab`, `inspector-note`, `inspector-layer-key`,
`inspector-turn`, `device-panel`, `orientation-right`, …); each stitch adds its
own. Captures go in the stitch's directory and the report names them.

### 4.13 Look

Light and dark, following glra-studio's `Main.qml` on 2026-11-13: a `dark`
property from the system scheme and a small palette (ink, muted, surface,
line, accent) defined once in `Main.qml`. Our own colours and wording; no
vendor app's look.

---

## 5. Lighting

Bob, 2026-11-13: "we also want to select the rgb mode from the factory
firmware." `glean:k16n3-lighting` holds the probe results this section relies
on (firmware 103, Bob's pad).

### 5.1 What the selector offers

All thirteen modes the probe found:

| Mode | Name | Brightness | Speed | One colour |
| --- | --- | --- | --- | --- |
| 0 | Off | — | — | — |
| 1 | Steady | ✓ | — | ✓ |
| 2 | Breathing | ✓ | ✓ | ✓ |
| 3 | Spectrum | ✓ | ✓ | — |
| 4 | Flow (rows) | ✓ | ✓ | ✓ |
| 5 | Flow (columns) | ✓ | ✓ | ✓ |
| 6 | Raindrop | ✓ | ✓ | ✓ |
| 7 | Meteor | ✓ | ✓ | ✓ |
| 8 | Starry sky | ✓ | ✓ | — |
| 9 | Ripples | ✓ | ✓ | — |
| 10 | Ripples 2 | ✓ | ✓ | — |
| 11 | Lit on press | ✓ | ✓ | ✓ |
| 12 | Custom (the pad's stored per-key colours) | ✓ | — | — |

The names for 4/5 and 9/10 are Claude's placeholders; the probe told the
variants apart only as "flows (whole rows/columns)" and "Ripples". Which
fields each mode reads (the ✓s for speed) were inferred, not verified per
mode; `lighting.py` marks them so, and the tour checks them (Q6). Custom
mode shows the pad's stored table; the app doesn't edit per-key colours
(dropped with `rgb-feedback`).

Brightness 0..4 and speed 0..4 as pickers. **Direction is not offered**: the
probe didn't verify it, so the app keeps whatever byte the pad holds (5.3).

### 5.2 In the profile

```toml
[lighting]
mode = 2
brightness = 4
speed = 2
color = [0, 255, 255]   # optional: h, s, v 0..255; only for modes marked "One colour"
```

`color` present = colour flag 1 and those HSV bytes; absent = flag 0. `color`
on a mode that doesn't take one is an error. The section is optional; with
none, the app's Apply stays disabled and shows "No lighting set in this
profile."

### 5.3 Write policy

- **One guarded write, only on [Apply to pad].** Never on drag, field change,
  Save, Open, app start, or `glra-osc run`. *Why:* each `06 0b` persists to
  flash (`glean:k16n3-lighting`).
- Apply reads the pad's current 11 bytes, builds the new payload by changing
  only mode, brightness, speed, colour flag and HSV (bytes 2, 3, 4, 6, 8–10),
  and keeps the rest as read (direction, byte 7). If the result equals what
  the pad holds, it writes nothing and says "Already set."
- Otherwise: backup (the vendored `lighting.py` path), write `06 0b`, exact
  readback, report. In a worker thread, as glra-studio's `worker.py` does.
- The button disables while a write runs and for a second after.
- Never `06 14`, never `06 12`, never past the 11 bytes.
- `glra-osc lights` prints the pad's mode; `glra-osc lights --apply` shows the
  change and asks before the same guarded write.

---

## 6. Orientation

Bob, 2026-11-13: "and have an orientation selector."

### 6.1 The four

The name says where the dials sit as Bob looks at the pad. Each rotates the
pad clockwise from the one before.

| Name | Rotation from dials-top | Dials sit |
| --- | --- | --- |
| `dials-top` (default) | 0° | along the top edge, as `layout.json` numbers them (as of 2026-11-12) |
| `dials-right` | 90° clockwise | down the right edge (the vendor's frame, as the flow animations suggest) |
| `dials-bottom` | 180° | along the bottom edge |
| `dials-left` | 270° clockwise | down the left edge |

### 6.2 Numbering

The physical id stays `layout.json`'s name: key k sits at physical row
`(k−1) // 4`, column `(k−1) % 4` with the dials along the top. A physical
(r, c) shows at:

| Orientation | Shown (row, col) |
| --- | --- |
| dials-top | (r, c) |
| dials-right | (c, 3 − r) |
| dials-bottom | (3 − r, 3 − c) |
| dials-left | (3 − c, r) |

The **displayed key number** counts the grid as shown: row by row from the
top-left, 1..16. **Dials** count left to right when along the top or bottom,
top to bottom when along the left or right:

| Orientation | Displayed D1, D2, D3 = physical |
| --- | --- |
| dials-top | enc.1, enc.2, enc.3 |
| dials-right | enc.1, enc.2, enc.3 (enc.1 at the top) |
| dials-bottom | enc.3, enc.2, enc.1 |
| dials-left | enc.3, enc.2, enc.1 (enc.3 at the top) |

Worked example, dials-right (physical key shown in each displayed cell):

```
            displayed columns →         dials
           1      2      3      4
row 1   key.13  key.9  key.5  key.1      D1 = enc.1
row 2   key.14  key.10 key.6  key.2      D2 = enc.2
row 3   key.15  key.11 key.7  key.3      D3 = enc.3
row 4   key.16  key.12 key.8  key.4
```

So in dials-right, displayed key 1 = `key.13`, displayed key 4 = `key.1`.

### 6.3 What follows the orientation

- The pad view's layout and every label in the app (tiles, inspector header,
  validation messages): "Key 1" means the displayed number.
- `monitor` and `run --dry-run` label events with displayed numbers when a
  profile is in use, physical id in brackets: `KEY 01 [key.13] DOWN`.
- **Not** the file: assignments stay on physical ids, so turning the pad
  remaps nothing (reading 8).
- **Not** cw/ccw: a clockwise turn is clockwise however the pad lies.
- **Not** the firmware animations: they run in the vendor's frame whatever the
  chosen orientation (a flow that runs left to right in dials-right runs top to
  bottom in dials-top).

---

## 7. Open questions for Bob

Listed with the default taken in
`.loom/threads/config-app/config-design.stitching/questions.md`. In short:
Q1 latch on CC momentary; Q2 one ease time both ways; Q3 the default
profile's layout; Q4 quadratic curves; Q5 global → per-layer copies to every
layer; Q6 lighting mode names and fields; Q7 profile location; Q8 the
starting layer. The tour lists them all.
