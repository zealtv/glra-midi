# app-review-polish: report (paused)

Worker: Claude Sonnet 5.5, 2026-11-13. Items go one per commit, cheapest first:
13, 11, 10, 8, 9, 12, 5, then the pad view shrinking.

## Done so far

- **13** `lighting.data_dir` calls `profile.app_dir` (commit `0afb051`). Test: both agree.
- **11** The parser refuses `[key."01"]`, `layers."01"`, `"+1"` (a table name must be the plain
  number) and `version = 1.0`. The shipped default profile, `demo_profile.toml` and every file in
  `tests/fixtures/` still load (checked by loading them, not only by the suite). CHANGELOG
  "Changed" says what now fails.
- **10** An invalid port draft counts as unsaved (title bullet, quit/Open ask) and blocks Save and
  Save As with "Fix the MIDI port before saving: …". I chose blocking over "Save writes the old
  port" because the latter leaves the app dirty after a successful Save.
- **9** `Controller.poll` returns early while `_confirmed` or `_after` is pending. Stamps stay
  stale, so the change is noticed on the first poll after the answer.

## Left to do

Paused at the manager's request (usage near the limit) after commit `f9eac61`; `./test.sh` passed
there (615 tests) and the tree was clean. No code for 8 or later is written yet. `.worker-done` is
not touched, and main is not yet merged into the branch.

- **8** Problems [Select] should switch the layer. Plan from what I read: `Main.qml:~189` calls
  `controller.selectControl(modelData.control)`. Add a `layer` field to each dict in the
  `problems` list in `Controller._refresh` (parse `_LAYER_IN_PATH` against the problem's message
  path; 0 when none, and only when 1..layer_count), plus a `selectProblem(index)` slot that sets
  `_tab` and `_selected` together; point the QML button at it. Test in `test_app_controller.py`
  (a problem at `key.N.layers.3…` moves the tab to 3). A problem with no layer in its path (for
  example "key 13 goes to layer 6") leaves the tab alone.
- **9** done; **10**, **11**, **13** done (above).
- **12** Move the QML-composed strings (`"default (" + n + ")"`, `"Layer " + n` in
  `Inspector.qml:~30,35`; sentences in `DevicePanel.qml:~205,215`) into `inspector.describe` and
  `_device_model`.
- **5** Tile summaries truncate (`KeyTile.qml:~81-85` elides line 1; `CC20 10↔120` shows as
  "CC20 10↔1…"). Shrink the font further or drop the space; check with
  `tools/app-capture.sh` on the cc-momentary state, light and dark.
- **Pad view shrinking** with the device panel open at the default window size: reproduce with
  `tools/app-capture.sh device-panel out.png`, then look at the PadView sizing in `Main.qml`.
- Then: merge main, rerun `./test.sh`, finish this report (what was built, how checked, open
  questions; none so far), commit, `touch .worker-done`.
