# config-app tour — for Bob at the pad

Prepared by the Opus orchestrator, 2026-11-13, after every config-app stitch,
the fresh Opus review (`config-app-review.tied/review.md`) and its two fix
stitches landed. Nothing in the unattended run wrote to the pad; step 3 holds
the first real lighting write, and it needs your yes to L1 first.

Setup, once, from the repo root:

```sh
.venv/bin/pip install -e '.[dev,gui]'
./test.sh
```

Your real profile folder is `~/Library/Application Support/glra-osc/`
(`profiles/`, `current`). `glra-osc config --demo` runs the app on a
throwaway folder with a fake pad if you want to look around first.

## 1. The app

1. `.venv/bin/glra-osc config` (or `glra-osc-config`). The first launch
   creates `profiles/default.toml` from your Q3 default: 3 layers, dial
   pushes select layers 1/2/3, keys play notes 36–51 on channel = layer.
   The toolbar should say "Pad: connected (103)" (a read, no write).
2. Click each tab: Global, 1, 2, 3. Check that dial pushes show 🔒 on every
   tab, the right dial's turn shows **G** (global), and keys show per-layer.
3. Edit one control of each kind in the inspector: a note (momentary and
   latch), CC momentary (low/high, rise ms, fall ms, curve), CC set, CC
   inc/dec (step, ease ms), and a layer key (set / inc / dec). Switch one
   control between "This layer" and "All layers" (global → per-layer copies
   the event to every layer, your Q5).
4. Add a layer, rename it, remove it (the remove asks when the layer holds
   events). Save; Save As… a second profile; Open… back to the first.

## 2. `glra-osc run` into a DAW or MIDI monitor

1. `.venv/bin/glra-osc run` (port "GLRA K16"). Optionally run
   `glra-osc run --dry-run` first to see events, layer changes and MIDI printed.
2. Each kind: notes (momentary, latch), CC momentary with a rise and a fall
   you can hear or watch, CC set, CC inc/dec with easing, relative dials
   (left, middle) and the absolute right dial.
3. Layers: dial pushes 1/2/3 switch layers; the channel follows the layer;
   a key held across a layer change still releases its own note.
4. Hot reload: with `run` playing, change something in the app and Save.
   `run` prints `# reloaded …`; held notes release; CC values carry over
   (fixed after the review: the right dial continues from where it was).
5. Stop with Ctrl-C; no stuck notes.

## 3. The first real lighting write (needs your yes to L1)

**L1 first:** the vendored glra-studio write only accepts firmware 100; the
app lets exactly your pad's fingerprint (firmware 103, PID 0x2475) through for
one write at a time (`lighting-modes.tied/questions.md`). The review judged
the shape acceptable (finding 7). Say yes or no.

1. Open the device panel (click the "▸ RGB: …" strip). Pick a mode (e.g.
   Breathing), Apply. The result line says "Applied and read back.", "Already
   set.", or, if the pad reads back differently, that it was written but read
   back differently (fixed after the review: it no longer says "Not applied"
   after a write).
2. Replug; check the mode survived.
3. Review check: set Breathing with no colour, then Flow (columns) with no
   colour (finding 2: does firmware 103 keep per-mode HSV?).
4. L3 check: set Off, then Breathing, and see that the animation looks as before.
5. Restore your own: Custom (mode 12) holds your red X (keys 1, 4, 6, 7, 10,
   11, 13, 16); the stock payload is `0100040403030008ffffff`
   (`glean:k16n3-lighting`).

## 4. Orientation

In the device panel, try Dials on Top / Right / Bottom / Left with the pad
turned to match. Key 1 should sit top-left as you hold it, dials numbered in
reading order, cw/ccw unchanged. The formulas came from the design, not a pad
test (`orientation.tied/report.md`).

## 5. Readings to check in use

The eight readings you accepted on 2026-11-13 (goal `instructions.md`, reading
2 as you corrected it): note momentary/latch; global = same on all layers, no
fall-through; dial turns mappable per layer; easing = time + curve; 1–8
layers, wrap, no MIDI on a layer change, latch per layer; the app edits a
profile and `run` plays and reloads it; lighting only on Apply; orientation
by physical position.

Your answers Q1–Q9 (`lore:2026-11-13-config-design-answers`) are built in;
the readings Claude took where your words left room, each to confirm:

- **Q1:** CC momentary keeps a latch option; old mapping files don't load.
- **Q2:** `rise-ms` and `fall-ms` share one curve.
- **Q3:** left/middle dials are relative CC 16/17 on channel = layer
  ("inc and dec on some cc"); right dial absolute CC 18, channel 1, global.
- **Q6:** lighting mode names and which modes offer speed/brightness are
  inferred; check them as you go through the modes.
- **Q7:** profiles in `Application Support/glra-osc/profiles/`, `current`
  names the active one ("application folder" read as Application Support).

Other questions, each with the default taken:

- **P1 + review finding 3** (`profile-model.tied/questions.md`): removing a
  layer leaves `layer-set` keys as they were, so a "layer-set 3" key ends up
  pointing at the old layer 4 without a warning. Reviewer suggests renumbering
  them with the layers and flagging keys that pointed at the removed one
  (about 10 lines). Yes / no?
- **P2:** lighting defaults brightness 4, speed 2 when omitted.
- **L2:** brightness/speed change only for modes that read them; HSV only
  when a colour is given.
- **Port on reload** (`runner-profile.tied/report.md`): a changed `[midi]
  port` doesn't reopen the port mid-run (it would drop the DAW connection);
  `run` prints a note to restart.
- **Apply as you type** (review 4b): each keystroke that parses goes into the
  profile, so typing 300 leaves note 30 with the field in red. Keep, or commit
  on Enter / focus loss?
- **Inspector width** for CC momentary (twelve rows; it scrolls): cramped?

## 6. Left for you

Review findings not fixed before the tour (`config-app-review.tied/review.md`):

- 5: tile summaries truncate ("CC20 10↔1…").
- 8: the Problems list's [Select] doesn't switch to the layer it names.
- 9: a confirm dialog open during a disk reload applies to the old profile.
- 10: an invalid port draft doesn't count as unsaved.
- 11: the parser accepts `[key."01"]` and `version = 1.0`.
- 12: a few strings composed in QML rather than Python.
- 13: two definitions of the app folder.

Noted by the orchestrator from the captures: with the device panel open, the pad view
shrinks a lot at the default window size (`fix-app-apply-and-quit.tied/captures/device-panel-apply-mismatch.png`).

Ideas noted as later (not built, per the goal's "Not in this thread"):
copy/paste of events, undo, pressing a pad control to select it in the editor,
an in-app run switch, a menu-bar app, a `.app` bundle, colour per layer
(`lore:2026-11-13-layer-colour-wear-estimate`), and after the tour
`loom:public-release` (rename to glra-midi, versioning, first public release).
