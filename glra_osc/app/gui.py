# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 GLRA Studio contributors
# The start-up shape (Basic style, QQmlApplicationEngine with a context property, grabWindow
# for captures) follows glra-studio's macropad/gui.py, taken at commit 33aa281.

"""Qt Quick start-up: `glra-osc-config`, `--demo` and `--capture` (docs/config-app.md 4.12)."""

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

from .. import profile as prof

HERE = Path(__file__).parent
QML = HERE / "qml" / "Main.qml"
DEMO_PROFILE = HERE / "demo_profile.toml"
EMPTY_PROFILE = "version = 1\n"
CAPTURE_DELAY_MS = 700


def demo_home():
    """A throwaway home holding the fixture profiles, so `--demo` never touches the user's own."""
    home = Path(tempfile.mkdtemp(prefix="glra-osc-demo-"))
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
    controller.removeLayer(5)  # empty, so it goes: the layer key now points past the count


def _empty(window, controller):
    controller.openProfile("empty")


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
    "problems": _problems,
    "dialog-unsaved": _unsaved,
    "dialog-remove-layer": _remove_layer,
    "dialog-open": _dialog("openDialog", "openList"),
    "dialog-save-as": _dialog("saveAsDialog", "openFor"),
}


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="glra-osc config", description="Edit a glra-osc profile: layers, events, orientation"
    )
    parser.add_argument("--demo", action="store_true", help="run on a throwaway fixture profile")
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
    app.setApplicationName("glra-osc config")
    app.setApplicationDisplayName("glra-osc config")
    home = demo_home() if args.demo else None
    try:
        scheme = "dark" if args.dark else "light" if args.light else "system"
        controller = Controller(home=home, poll_ms=0 if args.demo else 1000, scheme=scheme)
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
        for line in warnings:
            print(line, file=sys.stderr)
        del engine
        return 1 if warnings and args.capture else code
    finally:
        if home is not None:
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
