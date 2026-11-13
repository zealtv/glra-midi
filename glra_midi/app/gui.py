# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 GLRA Studio contributors
# The start-up shape (Basic style, QQmlApplicationEngine with a context property, grabWindow
# for captures) follows glra-studio's macropad/gui.py, taken at commit 33aa281.

"""Qt Quick start-up: `glra-midi-config`, `--demo` and `--capture` (docs/config-app.md 4.12)."""

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

from .. import lighting as lights
from .. import profile as prof
from . import device

HERE = Path(__file__).parent
QML = HERE / "qml" / "Main.qml"
DEMO_PROFILE = HERE / "demo_profile.toml"
EMPTY_PROFILE = "version = 1\n"
CAPTURE_DELAY_MS = 700


def demo_home():
    """A throwaway home holding the fixture profiles, so `--demo` never touches the user's own."""
    home = Path(tempfile.mkdtemp(prefix="glra-midi-demo-"))
    folder = prof.profiles_dir(home)
    folder.mkdir(parents=True)
    shutil.copy(DEMO_PROFILE, folder / "default.toml")
    (folder / "empty.toml").write_text(EMPTY_PROFILE, encoding="utf-8")
    (folder / prof.CURRENT_FILE_NAME).parent.mkdir(exist_ok=True)
    return home


def _select(*, tab=None, control=None, orientation=None):
    """A capture state that shows `tab`, selects `control` and turns the pad."""

    def apply(window, controller):
        if orientation:
            controller.setOrientation(orientation)
        if tab is not None:
            controller.selectTab(tab)
        if control:
            controller.selectControl(control)

    return apply


def _dialog(name, method):
    def apply(window, controller):
        from PySide6.QtCore import QMetaObject, QObject

        _select(tab=1)(window, controller)
        dialog = window.findChild(QObject, name)
        QMetaObject.invokeMethod(dialog, method)

    return apply


def _unsaved(window, controller):
    controller.renameLayer(1, "Drums 2")
    controller.requestQuit()


def _remove_layer(window, controller):
    controller.removeLayer(1)


def _problems(window, controller):
    from dataclasses import replace

    controller.selectTab(1)
    controller.setOrientation("dials-right")
    controller.addLayer()
    profile = controller.profile
    controls = dict(profile.controls)
    controls["enc.3.push"] = prof.LayerSet(layer=5)
    controller._edit(replace(profile, controls=controls))
    controller.removeLayer(5)  # empty, so it goes: the layer key lost its layer and is flagged


def _problem_selected(window, controller):
    _problems(window, controller)
    controller.selectControl("enc.3.push")


def _empty(window, controller):
    controller.openProfile("empty")


def _then(*steps):
    """A capture state that applies `_select` and then calls controller methods in order:
    each step is `(method name, *args)`."""

    def apply(window, controller):
        for name, *args in steps:
            getattr(controller, name)(*args)

    return apply


def _open_panel(window, controller):
    controller.wait_for_pad()  # the start-up read on the fake pad has landed
    window.setProperty("deviceOpen", True)


def _panel(*steps, orientation=None):
    """A capture state with the device panel open, after `steps` (each `(controller method,
    *args)`). Every pad call here goes to the `FakePad` a capture always runs on."""

    def apply(window, controller):
        _open_panel(window, controller)
        if orientation:
            controller.setOrientation(orientation)
        for name, *args in steps:
            getattr(controller, name)(*args)

    return apply


def _no_pad(window, controller):
    _open_panel(window, controller)
    controller.pad.connected = False
    controller.refreshPad()


def _already_set(window, controller):
    _open_panel(window, controller)
    controller.pad.payload = lights.build(controller.pad.payload, controller.profile.lighting)
    controller.refreshPad()
    controller.wait_for_pad()
    controller.applyLighting()


def _readback_error(window, controller):
    _open_panel(window, controller)
    controller.pad.error = ValueError("Lighting readback did not match what was written.")
    controller.applyLighting()


def _apply_mismatch(window, controller):
    """The write went out and the pad read back something else (the first real Apply may)."""
    _open_panel(window, controller)
    before = controller.pad.payload
    expected = lights.build(before, controller.profile.lighting)
    other = bytearray(expected)
    other[lights.HUE] = 0x80  # a cached hue the pad kept
    controller.pad.error = lights.WriteNotConfirmed(
        before.hex(),
        expected.hex(),
        bytes(other).hex(),
        "~/Library/Application Support/glra-midi/backups/20261113T120000.000000Z-lighting-before.json",
        "Lighting readback did not match.",
    )
    controller.applyLighting()


def _bad_port(window, controller):
    _open_panel(window, controller)
    controller.setPort("")


def _bad_note(window, controller):
    controller.selectTab(1)
    controller.selectControl("key.1")
    controller.setField("note", "300")


STATES = {
    "default": _select(),
    "empty": _empty,
    "layer-tab": _select(tab=1),
    "global-tab": _select(tab=0),
    "selection-key": _select(tab=2, control="key.2"),
    "selection-global": _select(tab=3, control="key.1"),
    "selection-layer-key": _select(tab=1, control="enc.3.push"),
    "selection-turn": _select(tab=1, control="enc.2.turn"),
    "selection-per-layer-on-global": _select(tab=0, control="key.2"),
    "orientation-right": _select(tab=1, control="key.13", orientation="dials-right"),
    "orientation-bottom": _select(tab=1, orientation="dials-bottom"),
    "orientation-left": _select(tab=1, orientation="dials-left"),
    "inspector-note": _then(("selectTab", 1), ("selectControl", "key.2")),
    "inspector-note-global": _then(("selectTab", 2), ("selectControl", "key.1")),
    "inspector-cc-momentary": _then(("selectTab", 2), ("selectControl", "key.2")),
    "inspector-cc-set": _then(("selectTab", 1), ("selectControl", "key.3")),
    "inspector-cc-step": _then(("selectTab", 1), ("selectControl", "key.4")),
    "inspector-layer-key": _then(("selectTab", 1), ("selectControl", "enc.3.push")),
    "inspector-turn-relative": _then(("selectTab", 1), ("selectControl", "enc.1.turn")),
    "inspector-turn-absolute": _then(("selectTab", 1), ("selectControl", "enc.2.turn")),
    "inspector-empty-key": _then(("selectTab", 3), ("selectControl", "key.6")),
    "inspector-global-tab": _then(("selectTab", 0), ("selectControl", "key.2")),
    "inspector-invalid": _bad_note,
    "inspector-make-global": _then(
        ("selectTab", 1), ("selectControl", "key.2"), ("setApplies", "global")
    ),
    "device-panel": _panel(),
    "device-panel-collapsed": _select(),
    "device-panel-spectrum": _panel(("setLightingMode", 3)),
    "device-panel-steady": _panel(("setLightingMode", 1), ("setLightingColor", False)),
    "device-panel-off": _panel(("setLightingMode", 0)),
    "device-panel-no-lighting": _panel(("setLightingMode", -1)),
    "device-panel-no-pad": _no_pad,
    "device-panel-applied": _panel(("applyLighting",)),
    "device-panel-already-set": _already_set,
    "device-panel-error": _readback_error,
    "device-panel-apply-mismatch": _apply_mismatch,
    "device-panel-bad-port": _bad_port,
    "device-orientation-top": _panel(orientation="dials-top"),
    "device-orientation-right": _panel(orientation="dials-right"),
    "device-orientation-bottom": _panel(orientation="dials-bottom"),
    "device-orientation-left": _panel(orientation="dials-left"),
    "problems": _problems,
    "problem-selected": _problem_selected,
    "dialog-unsaved": _unsaved,
    "dialog-remove-layer": _remove_layer,
    "dialog-open": _dialog("openDialog", "openList"),
    "dialog-save-as": _dialog("saveAsDialog", "openFor"),
}


def make_pad(demo):
    """The pad object for this run: the in-memory `FakePad` for `--demo` and every capture (no
    HID call can happen), the `RealPad` only for a plain launch. Making a `RealPad` opens
    nothing; its reads start with the controller, its one write only on [Apply to pad]."""
    return device.FakePad() if demo else device.RealPad()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="glra-midi config", description="Edit a glra-midi profile: layers, events, orientation"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="run on a throwaway fixture profile and a fake pad (no device I/O at all)",
    )
    parser.add_argument("--capture", choices=sorted(STATES), metavar="STATE", help="render a state")
    parser.add_argument("--out", metavar="PNG", help="where --capture writes its picture")
    parser.add_argument("--dark", action="store_true", help="force the dark scheme")
    parser.add_argument("--light", action="store_true", help="force the light scheme")
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.capture and not args.out:
        parser.error("--capture needs --out")
    if args.capture:
        args.demo = True
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        os.environ.setdefault("QT_QUICK_BACKEND", "software")
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

    from PySide6.QtCore import QTimer, QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickWindow  # noqa: F401 - registers the window type (grabWindow)

    from .controller import Controller

    app = QGuiApplication(sys.argv[:1])
    app.setApplicationName("glra-midi config")
    app.setApplicationDisplayName("glra-midi config")
    if not args.demo:
        message = prof.migrate_app_dir()  # the pre-rename folder, before the controller reads it
        if message:
            print(message, file=sys.stderr)
    home = demo_home() if args.demo else None
    try:
        scheme = "dark" if args.dark else "light" if args.light else "system"
        # `--demo` and every capture run on the in-memory FakePad: no HID call can happen. Only a
        # plain `glra-midi config` (no --demo) gets the RealPad, which reads the pad's state and
        # writes lighting only on an explicit [Apply to pad] click.
        pad = make_pad(args.demo)
        controller = Controller(
            home=home,
            poll_ms=0 if args.demo else 1000,
            scheme=scheme,
            pad=pad,
            cooldown_ms=0 if args.capture else Controller.APPLY_COOLDOWN_MS,
        )
        engine = QQmlApplicationEngine()
        warnings = []
        engine.warnings.connect(lambda items: warnings.extend(str(i) for i in items))
        engine.rootContext().setContextProperty("controller", controller)
        engine.load(QUrl.fromLocalFile(str(QML)))
        if not engine.rootObjects():
            for line in warnings:
                print(line, file=sys.stderr)
            return 1
        window = engine.rootObjects()[0]
        if args.capture:
            STATES[args.capture](window, controller)

            def capture():
                try:
                    out = Path(args.out).resolve()
                    out.parent.mkdir(parents=True, exist_ok=True)
                    if not window.grabWindow().save(str(out)):
                        raise RuntimeError(f"could not save {out}")
                finally:
                    window.setProperty("quitOk", True)  # a dirty state must not hold the exit
                    app.quit()

            QTimer.singleShot(CAPTURE_DELAY_MS, capture)
        elif args.smoke_test:
            QTimer.singleShot(1500, app.quit)
        code = app.exec()
        controller.shutdown()  # no pad call outlives the window
        for line in warnings:
            print(line, file=sys.stderr)
        del engine
        return 1 if warnings and args.capture else code
    finally:
        if home is not None:
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
