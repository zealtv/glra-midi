# SPDX-License-Identifier: GPL-3.0-only

import unittest

from . import qt_support  # noqa: F401 - skips this module without PySide6, sets up Qt
from .qt_support import make_home

from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from glra_osc import profile as prof
from glra_osc.app import gui
from glra_osc.app.controller import Controller


class QmlCase(unittest.TestCase):
    def setUp(self):
        self.home = make_home(self)

    def load(self, scheme="system", home=None):
        self.controller = Controller(home=home or self.home, scheme=scheme)
        self.engine = QQmlApplicationEngine()
        self.warnings = []
        self.engine.warnings.connect(lambda items: self.warnings.extend(str(i) for i in items))
        self.engine.rootContext().setContextProperty("controller", self.controller)
        self.engine.load(QUrl.fromLocalFile(str(gui.QML)))
        self.assertTrue(self.engine.rootObjects(), self.warnings)
        self.window = self.engine.rootObjects()[0]
        self.window.setProperty("quitOk", True)
        self.addCleanup(self.tear_down, self.engine, self.controller)
        QTest.qWait(50)
        return self.window

    @staticmethod
    def tear_down(engine, controller):
        """Delete the engine before the controller its bindings read, so nothing evaluates
        against a controller that is gone."""
        for obj in (engine, controller):
            obj.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def settle(self, ms=30):
        QTest.qWait(ms)

    def find(self, name):
        """The item (or object) called `name`: the visual tree first, since Repeater items
        aren't QObject children of what they sit in; dialogs and popups after."""

        def walk(item):
            if item.objectName() == name:
                return item
            for child in item.childItems():
                found = walk(child)
                if found is not None:
                    return found
            return None

        found = walk(self.window.contentItem()) or self.window.findChild(QObject, name)
        self.assertIsNotNone(found, name)
        return found

    def click(self, name):
        item = self.find(name)
        centre = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
        QTest.mouseClick(self.window, Qt.LeftButton, Qt.NoModifier, centre)
        self.settle()


class LoadTests(QmlCase):
    def test_loads_in_light_and_dark_with_zero_warnings(self):
        for scheme in ("light", "dark"):
            with self.subTest(scheme=scheme):
                window = self.load(scheme)
                self.assertIsInstance(window, QQuickWindow)
                self.assertEqual(window.title(), "glra-osc config — default")
                self.assertEqual(self.warnings, [])
                self.assertEqual(window.property("dark"), scheme == "dark")

    def test_every_tab_orientation_and_selection_binds_cleanly(self):
        self.load()
        c = self.controller
        for orientation in prof.ORIENTATIONS:
            c.setOrientation(orientation)
            for tab in range(0, c.layerCount + 1):
                c.selectTab(tab)
                for control in ("key.1", "key.2", "enc.3.push", "enc.2.turn", ""):
                    c.selectControl(control) if control else c.clearSelection()
                    self.settle(5)
        self.assertEqual(self.warnings, [])

    def test_an_empty_profile_and_a_profile_with_problems_load_cleanly(self):
        home = make_home(self, "version = 1\n")
        self.load(home=home)
        self.assertEqual(self.warnings, [])
        self.controller.selectControl("key.5")
        self.settle()
        self.assertEqual(self.warnings, [])

    def test_the_pad_view_places_the_dials_on_the_edge_the_orientation_names(self):
        self.load()
        dials, keys = self.find("dialBlock"), self.find("keyGrid")
        origin = QPointF(0, 0)
        for orientation, axis, dials_first in (
            ("dials-top", "y", True),
            ("dials-bottom", "y", False),
            ("dials-left", "x", True),
            ("dials-right", "x", False),
        ):
            with self.subTest(orientation=orientation):
                self.controller.setOrientation(orientation)
                self.settle()
                d, k = dials.mapToScene(origin), keys.mapToScene(origin)
                d, k = (d.y(), k.y()) if axis == "y" else (d.x(), k.x())
                self.assertEqual(d < k, dials_first)
        self.assertEqual(self.warnings, [])


class InteractionTests(QmlCase):
    def test_clicking_a_tile_selects_it(self):
        self.load()
        self.click("tile-key.4")
        self.assertEqual(self.controller.selected, "key.4")
        self.click("tile-enc.2.push")
        self.assertEqual(self.controller.selected, "enc.2.push")

    def test_clicking_a_tab_shows_that_layer(self):
        self.load()
        self.click("tab2")
        self.assertEqual(self.controller.tab, 2)
        self.click("tab0")
        self.assertEqual(self.controller.tab, 0)

    def test_add_layer_button(self):
        self.load()
        self.click("addLayer")
        self.assertEqual(self.controller.layerCount, 5)
        self.assertEqual(self.controller.tab, 5)

    def test_save_button_follows_dirty(self):
        self.load()
        save = self.find("saveButton")
        self.assertFalse(save.property("enabled"))
        self.controller.renameLayer(1, "Kit")
        self.settle()
        self.assertTrue(save.property("enabled"))
        self.click("saveButton")
        self.assertFalse(self.controller.dirty)
        self.assertFalse(save.property("enabled"))

    def test_prompts_open_the_dialogs(self):
        self.load()
        self.controller.removeLayer(1)
        self.settle()
        self.assertTrue(self.find("confirmDialog").property("visible"))
        self.controller.resolveConfirm(False)
        self.find("confirmDialog").close()
        self.controller.renameLayer(1, "Kit")
        self.controller.requestQuit()
        self.settle()
        self.assertTrue(self.find("unsavedDialog").property("visible"))

    def test_open_and_save_as_dialogs_open(self):
        self.load()
        QMetaObject.invokeMethod(self.find("openDialog"), "openList")
        self.settle()
        self.assertTrue(self.find("openDialog").property("visible"))
        QMetaObject.invokeMethod(self.find("saveAsDialog"), "openFor")
        self.settle()
        self.assertTrue(self.find("saveAsDialog").property("visible"))
        self.assertEqual(self.warnings, [])


if __name__ == "__main__":
    unittest.main()
