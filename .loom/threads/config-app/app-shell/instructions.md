# app-shell — the app window: pad view, layer tabs, open and save

Suggested model: Sonnet. Build to `docs/config-app.md` (wireframes there).

Start from `../glra-studio/macropad/gui.py` and `qml/` (GPL-3.0-only; record
what was taken in `THIRD_PARTY_NOTICES.md`). As of 2026-11-13 glra-studio's
venv ran PySide6 6.10.2 on Python 3.14.

- `glra_osc/app/` with a `gui` extra (`PySide6==6.10.2`) and a `glra-osc-config`
  entry point (plus `glra-osc config`). The CLI must still import without PySide6.
- A controller (`QObject`) over a `profile.Profile`: the model lives in Python,
  QML only shows it and calls slots. No profile logic in QML.
- Pad view: 16 key tiles and 3 dials (push and turn each selectable), placed by
  `orientation.py`. Each tile shows a summary of what it does on the shown
  layer (text per the design); empty, inherited-from-global and layer-select
  states look different.
- Layer tabs: Global, then 1..n; add, remove, rename. Selecting a tab shows that
  whole layer.
- Selecting a control highlights it and opens an (empty for now) inspector area.
- File: opens the user's profile (creating it from the default on first save),
  Open…, Save, Save As…, Revert; a dirty marker; unsaved-changes prompt on quit.
- No device access at all in this stitch.
- Light and dark, following glra-studio's approach.

Checks without a display (`QT_QPA_PLATFORM=offscreen`): a test that loads the
QML with zero warnings; controller tests for tabs, selection, dirty, save and
reload. `tools/app-capture.sh` renders named states to PNG (`grabToImage` or
`QQuickWindow.grabWindow`); put captures in this stitch's directory and name
them in the report so the manager can look at them.
