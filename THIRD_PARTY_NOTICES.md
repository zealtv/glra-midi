# Third-party notices

glra-midi is licensed GPL-3.0-only (see `LICENSE`).

## glra-studio

`glra_midi/device/` contains code copied from
[glra-studio](https://github.com/imolitor/glra-studio) (GPL-3.0-only),
Copyright (c) 2026 GLRA Studio contributors, taken at commit `33aa281`. The
files keep their SPDX and copyright headers. See `glra_midi/device/README.md` for
the file list. `lighting.py` (the factory lighting payload checks and guarded write)
was added on 2026-11-13 from the same commit.

`glra_midi/app/` (the configuration app) takes its start-up and look from glra-studio's
`macropad/` at the same commit (`33aa281`), GPL-3.0-only, Copyright (c) 2026 GLRA Studio
contributors. Taken, with changes, as of 2026-11-13:

| File here | From glra-studio | What was taken |
|---|---|---|
| `glra_midi/app/gui.py` | `macropad/gui.py` | The Basic Qt Quick Controls style, a `QQmlApplicationEngine` with the controller as a context property, `grabWindow` for captures and `--demo`. The controller itself is new. |
| `glra_midi/app/qml/Main.qml` | `macropad/qml/Main.qml` | The light/dark palette defined once in the window and the `ApplicationWindow` set-up. The layout is new. |
| `glra_midi/app/qml/KeyTile.qml` | `macropad/qml/KeyTile.qml` | The tile as a styled `Button` with a tooltip and accessible name. States, badges and text are new. |
| `glra_midi/app/qml/AppButton.qml` | `macropad/qml/StudioButton.qml` | The button's shape and states, recoloured from the window palette. |
| `tests/test_app_qml.py` | `tests/test_qml.py` | The offscreen set-up and the find-an-item-and-click pattern. |

The files above keep the glra-studio copyright line beside our SPDX line. Other files under
`glra_midi/app/` are new in this repository.

## Dependencies

Dependencies keep their own licences.

| Component | Version | Upstream |
|---|---|---|
| cython-hidapi (`hidapi`) | 0.15.0 | https://github.com/trezor/cython-hidapi |
| HIDAPI | bundled by cython-hidapi | https://github.com/libusb/hidapi#license |
| rtmidi2 | >=1.5.0 | https://github.com/gesellkammer/rtmidi2 |
| RtMidi | bundled by rtmidi2 | https://github.com/thestk/rtmidi |
| tomli-w | 1.2.0 | https://github.com/hukkin/tomli-w (MIT) |
| Qt for Python (`PySide6`, optional `gui` extra) | 6.10.2 | https://doc.qt.io/qtforpython-6/ (LGPL-3.0 / GPL-3.0; see also Qt's own notices) |

glra-midi is an independent community project, not an official product of
G-LRA or Apple. Device names identify compatibility.
