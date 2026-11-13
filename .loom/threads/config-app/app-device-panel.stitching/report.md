# app-device-panel: report

Worker: Claude (Sonnet 5.5), 2026-11-13. Branch `app-device-panel`, two commits on top of `95a61f4`
(plus this report). `main` had nothing new when I merged it ("Already up to date"). `./test.sh`
passes: 554 tests (494 before), ruff clean. I touched no `.loom` state outside this directory and
nothing under `glra_osc/device/`.

**Device safety, as the manager asked (2026-11-13):** no test, capture or run in this stitch
opened the real pad, and I never launched the app against it. Tests, `--demo` and every capture
run on `FakePad`. The `RealPad` class exists and is wired into a plain `glra-osc config` launch,
but nothing here has run it against hardware.

## What I built

- **Device panel** (`qml/DevicePanel.qml`, a collapsible strip at the bottom of `Main.qml`; click
  the one-line "▸ RGB: …" strip to open it):
  - *Orientation*: Top / Right / Bottom / Left buttons; the pad view redraws and renumbers at once
    (design 6). Labelled "Dials on", short names so they fit.
  - *MIDI port* (text field) and *Channel* (1..16). An empty port stays in the field with the
    profile's own message ("expected a non-empty string…") and never reaches the profile.
  - *Lighting*: a Mode selector over the thirteen factory modes plus a first entry **"Leave as it
    is"** (removes `[lighting]`; this is how a profile gets none and how it gets one later).
    Brightness and Speed (0..4) show only for modes that read them (`lighting.MODES`); "One colour"
    with hue, saturation and value sliders and a swatch shows only for modes that take one.
    No direction field.
  - *Pad*: the toolbar shows "Pad: connected (103)" or "Pad: not found"; the panel shows
    "Pad now: Flow (rows) (mode 4) · brightness 4 · speed 3". A **Read pad** button reads again.
  - *Apply to pad*: with the line "Each Apply is saved in the pad's memory." beside it, and a result
    line: "Applied and read back." / "Already set." / "Not applied: <the error text>". Disabled
    when the profile has no `[lighting]`, the pad is not found, a call is running, for 1 s after
    one, or the lighting fails `lighting.check`.
- **`glra_osc/app/device.py`**: the pad interface (`read()`, `apply(lighting, directory)`), with
  `FakePad` (in memory; records `reads`, `apply_calls`, `writes`; can be "not found" or raise),
  `NoPad` (the Controller's default: no I/O at all) and `RealPad` (via `lighting.connect`,
  `read_payload`, `apply`; each call opens the vendor interface non-exclusively and closes it).
- **`padworker.py`**: one worker thread for pad calls, as glra-studio's `worker.py` keeps its
  transactions on one thread; results return as a signal on the UI thread.
- **`devicepanel.py`** (pure, no Qt): lighting edits and the dict the QML reads.
- **Controller** (`controller.py`): `pad=` and `cooldown_ms=` arguments; slots `setLightingMode`,
  `setLightingLevel`, `setLightingColor`, `setLightingHsv`, `setPort`, `setChannel`, `refreshPad`
  and `applyLighting`. `applyLighting` is the only call that can write; nothing else in the app
  calls `pad.apply`.
- **`gui.py`**: `make_pad(demo)` picks `FakePad` for `--demo` and every capture, `RealPad` only for
  a plain launch. Fifteen new capture states (`device-*`, listed below).
- `AppChoice.qml` gained `labelWidth`; new `AppSlider.qml`. `docs/config-app.md` (4.2, 4.3, 4.10)
  records what I built and the window height.

## The rules as built

- Fields edit the profile only. No write on drag, field change, save, open, revert, a disk reload
  or start-up; the tests count `FakePad.apply_calls` and `writes` across those and find zero.
- **Apply sends what the panel shows, not the saved file** (unsaved edits included). Editing while a
  write runs does not change what was sent (the frozen `Lighting` is captured at the click).
- Reads happen at start, on **Read pad**, and no other time: no polling timer touches the pad
  (the 1 s poll in non-demo mode only stats profile files). After an Apply, "Pad now" updates from
  the write's readback; no extra read.
- "Already set." comes from `lighting.apply` (it reads, builds, compares and writes nothing,
  not even a backup). The controller always calls `apply` once per click, so the fake counts one
  call and no write for an unchanged payload.
- Backups go to `<app folder>/backups` (under the test home in tests).

## How I checked

- `tests/test_app_device.py` (48): pure edits (`devicepanel`); `FakePad`; `RealPad` with
  `lighting.connect` swapped for the existing Reader-level fake from `test_lighting.py` (read
  sends nothing and asks only opcode `06 0a`; apply is one guarded `06 0b` write, then "unchanged"
  with no second write); the controller with a `FakePad` (read at start; not found; refresh; each
  control edits the profile and leaves the pad untouched; Apply once; unchanged writes nothing;
  readback error shown, no retry; a click while busy ignored; cooldown; lighting problem blocks);
  two subprocess captures with the real device functions replaced by ones that raise.
- `tests/test_app_qml.py` (+12, offscreen, real mouse clicks and key presses on the window):
  zero QML warnings in light and dark across every mode and the no-pad, error, empty-port states;
  strip toggles the panel; Apply button calls the fake once, then "Already set."; opening the panel
  and clicking every field never calls `apply`; Apply disabled with no pad and with no lighting;
  orientation buttons turn the pad; colour switch and a slider (by keyboard) edit the profile;
  typing a port name, and an empty one.
- `forbid_real_device(testcase)` (in `tests/qt_support.py`) makes `backend.enumerate_devices`,
  `select`, `open_device` and `lighting.connect` raise; every `QmlCase` and every device test sets
  it up, so a stray real call fails the test.
- I looked at every capture in `captures/` (light; `device-panel-dark.png` for dark): `device-panel`,
  `-collapsed`, `-spectrum`, `-steady`, `-off`, `-no-lighting`, `-no-pad`, `-applied`,
  `-already-set`, `-error`, `-bad-port`, `device-orientation-top|right|bottom|left`.
- **Not checked:** a real on-screen launch (offscreen only); a real mouse in the drop-downs
  (popups opened by clicking never ran; the tests set values through slots); the hue scale (below).

## What needs the real pad (for the tour, with Bob watching)

1. **Does a read answer while `glra-osc run` is going?** The fake can't tell. `RealPad` opens the
   vendor interface non-exclusively, as `glra-osc lights` does, so I expect yes; if it fails the
   panel shows "Pad: not found", Apply stays off, and the rest of the app works.
2. **Apply on firmware 103** still hangs on lighting-modes' question **L1** (the widened firmware
   gate). Unanswered, an Apply on Bob's pad would show "Not applied: …" with the gate's message.
3. **Hue scale.** The swatch reads the hue byte as a fraction of the colour wheel (0..255 → 0..360°);
   the pad's own scale is unverified, so the swatch may not match the pad's colour. The tour can
   check hue 0, 85, 170 against the pad.
4. Whether a `FakePad`-style "Pad now" matches after a real Apply (readback text).

## What I didn't build

- No in-app run switch, no pad-key selecting, no per-key colours, no direction (all outside the
  thread, per `instructions.md`). No undo.
- The panel stays closed at start; its open/closed state isn't remembered between launches.
- `--smoke-test` without `--demo` would run the real start-up read; use it with `--demo`.

## Readings and choices where the design or stitch left room

1. **"Leave as it is"** as the selector's first entry: the stitch says Apply stays disabled with no
   `[lighting]` but gives no way to remove or add the section.
2. **Sliders for hue, saturation and value**, as design 4.10's wireframe shows, not hue only as the
   stitch text says (the design wins).
3. **Window height 640 → 740** so the pad view isn't squeezed with the panel open (design 4.3 says
   "about 1000 × 640"). Easy to change in `Main.qml`; the layout still scales the pad down.
4. **Orientation labels** "Top / Right / Bottom / Left" under "Dials on" (the wireframe's "Dials
   top" overflowed its buttons).
5. **Read pad** button and the read-only-at-start rule: the stitch asked to show the pad's current
   mode but not when to re-read.
6. **Port edits apply as you type**, like the inspector fields; an empty entry stays in the field.

## Open questions

None that block; no `questions.md`. For the tour: items 1–3 under "What needs the real pad", and
whether 740 px of window height is acceptable on Bob's screen.
