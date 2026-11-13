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


class InspectorTests(QmlCase):
    def select(self, control, tab=1):
        self.controller.selectTab(tab)
        self.controller.selectControl(control)
        self.settle()

    def type_into(self, name, text):
        field = self.find(name)
        self.click(name)
        QMetaObject.invokeMethod(field, "selectAll")
        for char in text:
            QTest.keyClick(self.window, char)
        self.settle()

    def test_every_kind_and_state_binds_cleanly(self):
        self.load()
        c = self.controller
        for tab in (0, 1, 2):
            for control in ("key.1", "key.2", "key.4", "key.6", "enc.3.push", "enc.1.turn", "enc.2.turn"):
                self.select(control, tab)
        self.select("key.9")
        for kind in ("note", "cc-momentary", "cc-set", "cc-step"):
            c.setAction("event")
            c.setKind(kind)
            c.setField("note" if kind == "note" else "cc", "300")  # an error showing, too
            self.settle(5)
        self.select("enc.3.push")
        c.setLayerKey("layer-set", 2)
        self.settle(5)
        self.assertEqual(self.warnings, [])

    def test_typing_a_number_edits_the_profile(self):
        self.load()
        self.select("key.1")
        self.type_into("field-note", "60")
        self.assertEqual(self.controller.profile.controls["key.1"].note, 60)
        self.assertEqual(self.find("field-note").property("text"), "60")

    def test_typing_an_invalid_number_shows_the_message_and_keeps_the_profile(self):
        self.load()
        self.select("key.1")
        self.type_into("field-note", "300")
        # Typed digit by digit, "3" and "30" were fine and applied; "300" is not and stayed out.
        self.assertEqual(self.controller.profile.controls["key.1"].note, 30)
        self.assertEqual(self.find("field-note").property("text"), "300")
        error = self.find("error-note")
        self.assertTrue(error.property("visible"))
        self.assertEqual(error.property("text"), "expected an integer 0..127, got 300")

    def test_the_action_buttons_switch_between_event_layer_and_none(self):
        self.load()
        self.select("key.9")
        self.click("seg-action-event")
        self.assertEqual(self.controller.profile.controls["key.9"].get(1), prof.Note(note=36))
        self.click("seg-action-none")
        self.assertNotIn("key.9", self.controller.profile.controls)
        self.click("seg-action-layer")
        self.assertEqual(self.controller.profile.controls["key.9"], prof.LayerInc())
        self.assertTrue(self.find("layerKeyFields").property("visible"))
        self.click("seg-layerkey-layer-dec")
        self.assertEqual(self.controller.profile.controls["key.9"], prof.LayerDec())

    def test_the_applies_buttons_switch_global_and_per_layer(self):
        self.load()
        self.select("key.1", 2)
        self.click("seg-applies-layer")
        self.assertIsInstance(self.controller.profile.controls["key.1"], prof.PerLayer)
        self.click("seg-applies-global")
        self.settle()
        self.assertEqual(self.controller.profile.controls["key.1"], prof.Note(note=36, velocity=110))

    def test_a_per_layer_control_on_the_global_tab_shows_make_global(self):
        self.load()
        self.select("key.2", 0)
        self.assertTrue(self.find("eachBox").property("visible"))
        self.assertFalse(self.find("eventFields").property("visible"))
        self.click("makeGlobal")
        self.assertTrue(self.find("confirmDialog").property("visible"))
        self.controller.resolveConfirm(False)
        self.find("confirmDialog").close()

    def test_a_click_on_also_on_jumps_to_that_layer(self):
        self.load()
        self.select("key.2", 1)
        self.click("alsoOn2")
        self.assertEqual(self.controller.tab, 2)

    def test_the_latch_switch_edits_the_event(self):
        self.load()
        self.select("key.9")
        self.click("seg-action-event")
        self.click("field-mode")
        self.assertEqual(self.controller.profile.controls["key.9"].get(1).mode, "latch")
        self.click("field-mode")
        self.assertEqual(self.controller.profile.controls["key.9"].get(1).mode, "momentary")

if __name__ == "__main__":
    unittest.main()
