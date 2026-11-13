# app-shell: report

Worker: Claude (Sonnet 5.5), 2026-11-13. Branch `app-shell`, three commits plus the merge of
`main` (as of the merge `main` held `runner-profile`). `./test.sh` passes after the merge:
423 tests, ruff clean. I touched no `.loom` state and nothing under `glra_osc/device/`, and the
app does no device I/O.

## What I built

- **Packaging.** `gui` extra (`PySide6==6.10.2`), entry points `glra-osc-config`
  (`glra_osc.app:main`) and `glra-osc config` (the CLI hands everything after `config` to the
  app). `glra_osc/app/__init__.py` imports Qt only inside `main()`; without PySide6 it prints
  `pip install 'glra-osc[gui]'` and exits 2. A test imports the CLI and `summary.py` in a
  fresh interpreter and checks no PySide6 module loads.
- **`glra_osc/app/summary.py`** (pure): `note_name` (C1 = 36), `summarize` (two lines for every
  event kind, per design 4.4; `ch N` only when it differs from `[midi] channel`) and
  `tile_info` (state, badge, lines, "n of m" for per-layer controls on the Global tab).
- **`glra_osc/app/controller.py`**: `Controller(QObject)` over `profile.Profile`. Layer tabs
  (Global, 1..n), selection, layer add/remove/rename (remove asks when the layer holds events),
  `setOrientation`, the inspector's text, validation problems (messages carry displayed
  numbers, e.g. `Dial 3 push (layer): layer 5 doesn't exist (count = 4)`; Save is blocked while
  any exist), and the file operations of §4.8: start on `current_profile_path()`, Open… (lists
  `profiles/`, calls `set_current`), Save, Save As… (checks the name, asks before replacing,
  calls `set_current`), Revert, a Save / Don't save / Cancel prompt on quit and Open…, and
  reload when the open file or `current` changes on disk (`poll()`, run every second; unsaved
  edits get a "changed on disk" notice with [Reload] / [Keep mine]).
- **QML** (`glra_osc/app/qml/`): `Main.qml` (toolbar, banners, tabs, pad, inspector, one-line
  device strip, dialogs; the palette defined once, light and dark following the system),
  `PadView.qml` (keys and dials placed by orientation, scaled down in small windows),
  `KeyTile.qml`, `DialTile.qml`, `LayerTabs.qml`, `Inspector.qml`, `AppDialog.qml`,
  `AppButton.qml`. The five tile states differ by badge as well as colour: empty `—`,
  per-layer event (plain), global (`G`), layer key (`🔒`), and the Global tab's per-layer tile
  (dimmed, `≠`, "per layer", "2 of 4").
- **`--demo` and `--capture`**: `glra-osc config --demo` runs on a throwaway home holding
  `glra_osc/app/demo_profile.toml` (the §2.5 example) and `empty.toml`, so it never touches
  `~/Library/Application Support/glra-osc/`. `tools/app-capture.sh <state> <out.png> [--dark]`
  renders a state offscreen; `python -m glra_osc.app --help` lists the 17 states.
- `THIRD_PARTY_NOTICES.md` records what came from glra-studio (`gui.py`, `Main.qml`,
  `KeyTile.qml`, `AppButton.qml`, the QML test pattern) and adds PySide6. README and AGENTS.md
  now say `.[dev,gui]`.

## Captures (in `captures/` beside this report)

Orientations: `orientation-right.png` (displayed key 1 = `key.13`, selected), `orientation-bottom.png`,
`orientation-left.png`. Tabs and tiles: `layer-tab.png`, `layer-tab-dark.png`, `global-tab.png`,
`default.png`, `empty.png`. Selection: `selection-key.png`, `selection-global.png`,
`selection-layer-key.png`, `selection-turn.png`, `selection-per-layer-on-global.png`.
Messages and dialogs: `problems.png`, `dialog-unsaved.png`, `dialog-remove-layer.png`,
`dialog-open.png`, `dialog-save-as.png`.

## How I checked

- `summary.py`: unit tests for every kind, the channel rule, note names and each tile state.
- Controller (52 tests, offscreen, temp home): tabs, selection, orientation, layer edits and
  their prompts, dirty, save, save as, open, revert, quit, reload and keep-mine, a broken file
  at start-up and mid-session.
- QML (10 tests): loads with zero warnings in light and dark; every orientation × tab × selection
  binds without a warning; real clicks on tiles, tabs, `+` and Save; the dialogs open;
  the dial block sits on the edge the orientation names.
- Without PySide6 the two app test modules skip and the rest passes (checked by blocking the import).
- I looked at the captures myself. Not checked: a real on-screen launch (everything ran
  offscreen); the first look at it belongs to the manager or Bob.

## What I didn't build

No editing fields (the inspector names the selected control and shows its summary), no
device panel, no orientation control (the slot `setOrientation` exists and the file's
`[pad] orientation` works; the picker belongs to `app-device-panel`), no Apply, no device
access, no undo, no profile rename or delete. The strip at the bottom is one line from the
profile (RGB mode name, orientation, port, channel); it doesn't expand and shows no "Pad:"
state.

## Readings and choices where the design or stitch left room

1. **Revert** asks with a Yes/No ("Throw away the unsaved changes to X?") rather than the
   Save / Don't save / Cancel prompt, since §4.8 first says "after a confirm" and then lists
   Revert with quit and Open…; offering Save on Revert makes no sense. Quit and Open… use the
   three-way prompt. Easy to flip.
2. **Comments notice at open.** §2.8 says the app "warns once per file when the file it opened
   contained comments"; I show a dismissible banner when a file opens. Because
   `profiles/default.toml` starts as a copy of the commented shipped default, a first-time
   user sees it on the first launch (see the captures). Bob may find that noisy.
3. **A broken current profile at start-up**: the app shows the error and an empty profile,
   disables Save (so the broken file isn't overwritten) but leaves Save As… and Open… working.
4. **Start tab** is layer 1, not Global.
5. **Global-tab count** in the empty inspector reads "6 of 22 controls act the same on every
   layer"; 22 is every control (16 keys, 3 pushes, 3 turns), where the wireframe says 19.
6. **Problem text**: `Dial 3 push (layer): …`; the field in brackets is the tail of the key path.
7. Added a **Remove…** button beside Rename… (the design offers right-click only).
8. Dial captions read `D1` (push) and `D1 turn`, to leave room on the round tile.
9. `Cmd+S`, `Cmd+O` and `Cmd+Shift+S` work.
10. Reload uses a 1 s poll of mtime, size and inode instead of QFileSystemWatcher, which
    loses its watch when a file is replaced by rename (as `dump_profile` does).
11. Dark/light follows the system scheme; `--dark` / `--light` force it for captures. There
    is no toggle button (glra-studio has one).

## Open questions

None that block. `questions.md` not written. Worth Bob's eye on the tour: items 1 and 2.

## Notes for `app-inspector`

Selection is by physical control name (`controller.selectControl("key.13")`); the displayed
label comes from `orientation.label`. Edits should go through a controller slot that calls
`profile.py`'s helpers and then `self._edit(new_profile)`, which refreshes the tiles and the
dirty flag (dirty is `profile != baseline`, so editing a field back clears it). In the QML
tests find items with a visual-tree walk, not `findChild`.
