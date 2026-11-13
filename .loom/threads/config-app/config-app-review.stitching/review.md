# config-app-review: review

Claude (Opus 5.5, fresh worker session), 2026-11-13. Review only: no code changed.

**Read:** `git diff 19faa3c..efdec05` (efdec05 = HEAD of `config-app-review` when I started, and
`main` had no newer commits), every `report.md` (and the `questions.md` files) under
`.loom/threads/config-app/*.tied/`, `docs/config-app.md`, the thread and stitch
`instructions.md`, and Bob's brief (`lore:2026-11-13-config-app-brief`). I read
`engine.py`, `profile.py`, `runner.py`, `lighting.py`, vendored `device/lighting.py`, `cli.py`,
`monitor.py`/`events.py` changes, and all of `glra_osc/app/` (Python closely, QML for logic
it shouldn't hold). `./test.sh` at efdec05: ruff clean, 554 tests OK.

Probes run (scratch script, outside the repo, fakes only, no device I/O) are marked
**verified**. Findings I reasoned out but didn't reproduce are marked **plausible**.

## Findings, most severe first

### 1. A profile reload wipes the engine's CC values and CC latches. Fix before the tour.

`glra_osc/runner.py:159` builds a fresh `Engine` on every reload, and `glra_osc/engine.py:105-116`
starts it with an empty `_cc` table (re-seeded only from `initial`) and no `_latched_ccs`.
Design 3.4 says the value table survives layer changes and `release_all`. A reload behaves
as a cold start, and on the tour a reload happens on every Save in the app while `run` plays.

- **Verified:** the default profile's right dial (`enc.3.turn`, CC 18, `initial = 64`) turned up
  five detents sends 65..69. After `Engine(p, layer=e.layer)` the next detent sends **65**, so the
  value jumps back about 4 steps. With no `initial`, a CC drops to 0/1.
- `cc-step` keys build on 0 (or `initial`) again, not on what the DAW last received.
- A latched `cc-momentary` sitting at `high` (which `release_all` keeps, 3.7) is "unlatched" in
  the new engine. The next press re-sends `high` (or glides from 0 when `rise-ms` > 0, which is
  audible), and only the second press brings it down.

Suggested fix (small): let `Engine` take the old engine's `_cc` (for example
`Engine(new, layer=..., carry=old_engine)`), and keep `_latched_ccs` entries whose
(control, layer) still holds an equal latched `cc-momentary` in the new profile. Seed `initial`
only for pairs the old table lacks. A test: turn, reload, turn sends value+1.

### 2. The first real lighting Apply may report "Not applied" after it did write. Fix the wording before the tour.

Vendored `glra_osc/device/lighting.py:111-114` excuses an HSV readback difference only for
modes 2 and 4 with the colour flag 0 ("animated modes retain per-mode HSV caches", seen on
firmware 100). `glra_osc/lighting.py:build` (line 166) writes flag 0 and leaves the HSV bytes
as read whenever the profile has no `color`. If firmware 103 also keeps a per-mode HSV cache
for other modes (1, 5-7, 11 take a colour), the write lands, the readback differs, and
`write` raises `"Lighting readback did not match. Further writes are paused."`. The app then
shows `Not applied: …` (`glra_osc/app/controller.py:623`). Both halves of that message would be
wrong: the pad was written, and nothing pauses later writes. **Plausible**: no probe has
checked HSV readback on modes other than 2/4 on firmware 103.

Since this is the first real write, with Bob watching, I'd fix the message before the tour,
not the tolerance. In `glra_osc/lighting.apply` (or `RealPad.apply`), catch a `RuntimeError`
raised after the write and say "Written, but the pad read back something different: <before /
expected / after>. Backup: <path>". Say "Not applied" only when nothing was sent. Also put "set
Breathing with no colour, then Flow (columns) with no colour" on the tour's check list.

### 3. Removing a layer silently retargets the `layer-set` keys that point above it. Bob decides at the tour (P1).

`glra_osc/profile.py:985-1015` renumbers per-layer events down, but leaves `LayerSet.layer` as
it was. Only keys that end up past the new count are flagged. With 4 layers and a key on
"layer-set 3", removing layer 2 makes that key go to what used to be layer 4, with no
problem listed. The confirmation (`controller.py:659-664`) only counts discarded events.
Design 4.7 flags past-count keys only, and `profile-model.tied/questions.md` P1 is still
open. **Verified** for the past-count case; the in-range retarget follows from the code. I'd
suggest renumbering `n > removed` to `n - 1` and flagging `n == removed`. That matches what
happens to the events, so a key keeps pointing at the same content. Put it to Bob with P1;
the fix is about 10 lines if he agrees.

### 4. Inspector: the note-name hint follows the profile, not the field; and apply-as-you-type. Fix the hint before the tour, and put the rest to Bob.

- `glra_osc/app/inspector.py:205-206` computes `noteName` from `action.note`, the value in the
  profile, while the field shows a draft. Typing `300` leaves the profile at 30 (see below), so
  the hint reads the name of 30 beside "300" (the orchestrator saw "C1" in
  `app-inspector.tied/captures/inspector-invalid.png`). Fix: blank the hint when
  `drafts["note"]` carries an error.
- Apply-as-you-type (`app-inspector.tied/report.md` reading 1): every keystroke that parses
  reaches the profile. Typing 300 ends with the profile on note 30 and the field showing 300 in
  red. After a click elsewhere the drafts drop (`controller.py:340-342`) and the field
  silently shows 30. A partial value can then be saved and played. The same applies to
  `initial`, where a half-typed number can raise a cross-check problem for a moment. Tour item
  for Bob: keep it, or commit on Enter or focus loss.

### 5. Tile summaries truncate. Tour list (cosmetic).

`glra_osc/app/qml/KeyTile.qml:81-85` elides line 1, so `CC20 10↔120` shows as "CC20 10↔1…"
(the orchestrator's note, `inspector-cc-momentary.png`). The font step-down at more than 11
characters isn't enough. A cheap fix is to drop the "CC" space or let line 1 shrink further.
Not blocking.

### 6. Quitting during an Apply write. Cheap fix; I'd do it before the tour.

`Main.qml:46-53` `onClosing` checks only `dirty`, and `PadWorker.shutdown`
(`glra_osc/app/padworker.py:46`) is never called. If Bob closes the window while the one
write runs, the worker thread keeps going (executor threads are joined at interpreter exit,
so the write very likely finishes), but `done` then emits into a controller Qt may already
have destroyed, and nobody sees the result. **Plausible.** Fix: refuse to close (or wait)
while `device.apply.busy`, and call `shutdown` from `gui.main` after `app.exec()`.

### 7. Firmware-103 gate (`lighting.apply` widening the vendored checks): the shape is acceptable. No change needed; L1 still needs Bob's yes.

The orchestrator asked me to judge this. `glra_osc/lighting.py:216-244`:

- Under a module lock, it widens `device/lighting.MODES` and swaps
  `transactions.validate_status` for one that lets exactly `BOB_PAD` through. For that
  fingerprint it repeats the original profile/layer check (`transactions.py:18-24`), and any
  other pad goes to the original. Both are restored in `finally`. Tests cover success,
  failure, firmware 104 and firmware 100.
- It fails closed. If a later glra-studio sync made `device/lighting.py` bind
  `validate_status` by name (`from .transactions import validate_status`), the patch would
  stop taking effect, and the original check would refuse Bob's pad. It would not let some
  other pad through.
- Weakness: it is a process-global monkeypatch. Any other thread calling
  `transactions.validate_status` inside the window would see the widened check. Nothing does
  today: the app has one pad worker, and the CLI has one thread. An explicit `validate=`
  parameter would be cleaner, but it means editing vendored code, which the device README
  avoids for good reason. Keep the gate. L1 (`lighting-modes.tied/questions.md`) is still
  Bob's to approve before the first write.

### 8. Problems list [Select] doesn't switch to the layer the problem names. Tour list.

`Main.qml:189-192` calls `selectControl(control)` only. For a problem at
`key.4.layers.3…`, the tab stays where it was, so the inspector can show a different layer
than the one with the problem. The layer number is already parsed in
`controller._display_message` (`_LAYER_IN_PATH`). A `selectProblem(index)` slot could set
both the tab and the control.

### 9. Stale confirm after a disk reload. Low; after the tour.

`controller.py:706-713` and `:660` store a lambda that holds the edited profile, computed
when the prompt opened. With no unsaved edits, the 1 s `poll` can reload the file from disk
while the confirm dialog is open. "OK" then applies an edit built on the old profile,
dropping the reload. Fix: skip `poll` while `_confirmed` or `_after` is pending.

### 10. An invalid port draft doesn't count as unsaved. Low.

`controller.py:564-578`: an empty port stays in the field, but `is_dirty` compares only
profiles. The title shows no `•`, quitting doesn't ask, and Save writes the old port while the
field shows "". The error under the field makes this visible, so it's minor.

### 11. The parser accepts aliases. Low; after the tour.

**Verified:** `[key."01"]` parses as `key.1`, and when both appear the later table wins with
no error (`profile.py:557`; per-layer `layers."01"` at `:466`). `version = 1.0` passes
(`:570`, float equals int). Requiring `str(int(name)) == name`, and an int type for
`version`, would close both.

### 12. QML builds a few strings itself. Minor; after the tour.

Design 4.1 keeps text in Python. The QML holds no profile logic (it only branches on states
and kinds the controller hands it), but it composes `"default (" + n + ")"` and
`"Layer " + n` (`Inspector.qml:30,35`) and sentences in `DevicePanel.qml:205,215`. Cheap to
move into `inspector.describe` and `_device_model` when someone is next in there.

### 13. Two definitions of the app folder. Nit.

`lighting.data_dir` (`lighting.py:266`) repeats `profile.app_dir`. Both use `APP_DIR_NAME`,
so the glra-midi rename still touches one constant. `data_dir` could simply call `app_dir`.

## Checked and found sound

- **Nothing writes to the pad except Apply.** The only call paths to `_studio.write` are
  `lighting.apply`, reached from `RealPad.apply` (from `Controller.applyLighting`, from the
  [Apply to pad] button, gated by `_can_apply`, busy and a 1 s cool-down) and from
  `lights_command` after a typed `y`. `--demo` and every capture use `FakePad` and a throwaway
  home (`gui.py:26-34, 199-203`). `run`, Save, Open and start-up never call it. Reads go
  through the allowlisted `Reader.query` (status `05`, lighting `0a`). `silence.py`'s `apply`
  is a hidutil mapping, not a pad write.
- **Engine across layer changes:** a release goes to the binding its press made
  (`_down` holds the event). Latches are per (control, layer). Layer keys send nothing.
  inc/dec wrap, and `count = 1` stays put. `release_all` turns off held and latched notes,
  takes held `cc-momentary` to `low`, takes glides to their targets, and keeps CC latches.
  After `release_all`, an up for a forgotten down is ignored, so a reload or replug leaves no
  stuck notes.
- **Glides:** one glide per (channel, cc). Retargeting starts from the last sent value. A 0 ms
  time jumps from `handle`. It ends exactly on the target. `_cancel` clears `next_due` when
  the last glide goes. The tick clock and the report times are both `time.monotonic`, so
  they agree. I found no path that leaves a glide running with `next_due` None.
- **Files:** every write goes through `_write_atomic` (temp file in the same folder, fsync,
  chmod, `os.replace`). `current` is written only when missing, or by `set_current` on
  Open and Save As, as design 2 and 4.8 say. `default.toml` is never overwritten. A
  start-up read failure blocks plain Save, so a broken hand-edited file is never overwritten.
  Old mapping files fail on `version` with the design's message, and `mapping.py` is gone.
- **Against Bob's brief, line by line:** layer set/inc/dec, global by construction. Events with
  a layer (n or global) and a channel. Note momentary/latch, CC momentary with low/high and
  easing (separate rise and fall, Q2), CC set, CC inc/dec with easing. A layer tab bar that
  shows a whole layer. The factory RGB mode selector. The orientation selector. glra-studio as
  the base (vendored, GPL notices). The Q3 default profile matches Bob's words. "inc and dec
  on some cc" for the left and middle dials is read as `cc-relative`, which is the natural
  reading; still worth one line on the tour.

## For the manager

Before `config-app-tour`, I'd queue these small stitches: **1** (CC state across reload),
**2** (honest message after a write whose readback differs), **4a** (note hint) and **6**
(no quit mid-write). For the tour list, for Bob: **3** (with P1), **4b** (apply-as-you-type),
**5**, **8**, and L1/L2/L3 and Q6 as already planned. **9-13** can wait until after the tour.
