# config-design — settle the design in `docs/config-app.md`

Suggested model: Opus (the orchestrator itself, or an Opus worker). No Bob needed.

Read Bob's brief (`lore:2026-11-13-config-app-brief`) and the readings in the
goal's `instructions.md`. Write `docs/config-app.md`, the one design every
later stitch builds to. Then re-read each later stitch's `instructions.md`
against it and correct them where the design moved (they hold Claude's
2026-11-13 defaults).

Cover, each with a decision and a sentence of why:

1. **References** (desk, an hour at most): how Novation Components, Akai's MPK
   mini editor, Arturia MIDI Control Center, Intech Grid Editor and Elgato
   Stream Deck lay out "pick a control, edit it, switch layer/page". Note what
   to borrow; save links and notes in `references.md` here. Don't copy looks or assets.
2. **Profile format**: schema for layers, layer-select actions, events (layer n
   or global, channel, the four press kinds), encoder turns, lighting,
   orientation, port. Give a full example file. Decide the file type: default
   is TOML, written with `tomli-w` (a new dependency; `tomllib` only reads),
   at `~/Library/Application Support/glra-osc/profile.toml`. Today's mapping
   files (`glra_osc/default_mapping.toml`) must still load.
3. **Engine semantics**: resolution (a layer action, else the global
   event of a global control, else the active layer's event, else nothing; a
   control is global or per-layer, never both, with no fall-through, per Bob's
   2026-11-13 correction); what a layer switch does to held notes, held
   momentary CCs and running glides (default: a press releases through the
   binding it started with); per-layer latch state; one CC value table per
   (channel, cc) shared by set, inc/dec, momentary and absolute dials; easing
   curves, timing model (`tick(now)`), tick rate (default 100 Hz while a glide
   runs), what a second press during a glide does; inc/dec step, clamp,
   wrap of layer inc/dec.
4. **App**: PySide6 6.10.2 + Qt Quick, starting from `../glra-studio/macropad/`
   (`gui.py`, `qml/`; GPL-3.0-only, same as here). One window: pad view (16
   keys, 3 dials, drawn in the chosen orientation), layer tabs ("Global", 1..n,
   add/remove/rename), an inspector for the selected control, a device panel
   (RGB mode, orientation, port). Give a wireframe for each state (ASCII is
   fine), the tile summary text for each action kind, how a layer-select key
   shows on every tab (locked), how a global event shows on each layer
   tab (marked global), what switching a control between global and per-layer does, dirty/save/revert, validation messages. Module layout under
   `glra_osc/app/`; how the app gets tested without a display
   (`QT_QPA_PLATFORM=offscreen`) and how screenshots get captured for review.
5. **Lighting**: which firmware modes and parameters the selector offers
   (`glean:k16n3-lighting` lists modes 0–12 and the 11-byte payload), where the
   choice lives in the profile, and the write policy (one guarded write on
   Apply; never on drag).
6. **Orientation**: the four rotations, the default (dials along the top, as
   `layout.json` numbers them today), and how numbering, dial order and labels
   follow. Keep cw/ccw physical.
7. **Open questions for Bob**: `questions.md` here, each with the default taken.

Done when: `docs/config-app.md` and `references.md` exist, later stitches agree
with the doc, `./test.sh` passes (docs only, so it should be untouched).
