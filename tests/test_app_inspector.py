# SPDX-License-Identifier: GPL-3.0-only

"""The inspector through the controller's slots (offscreen): each action kind, the layer-key
rule, global <-> per-layer both ways, and invalid input staying out of the profile."""

import unittest

from . import qt_support  # noqa: F401 - skips this module without PySide6, sets up Qt
from .qt_support import make_home

from glra_midi import profile as prof
from glra_midi.app.controller import Controller

START = """
version = 1
[layers]
count = 3

[key.1]
kind = "note"
note = 36

[key.2.layers.1]
kind = "note"
note = 37

[key.2.layers.2]
kind = "cc-set"
cc = 21
value = 64

[enc.2.turn.layers.1]
kind = "cc-absolute"
cc = 21
step = 2
"""


class InspectorCase(unittest.TestCase):
    text = START

    def setUp(self):
        self.home = make_home(self, self.text)
        self.c = Controller(home=self.home)
        self.addCleanup(self.c.deleteLater)
        self.prompts = []
        self.c.confirmPrompt.connect(lambda title, text: self.prompts.append((title, text)))

    def pick(self, control, tab=1):
        self.c.selectTab(tab)
        self.c.selectControl(control)

    def event(self, control, layer=None):
        value = self.c.profile.controls.get(control)
        return value.get(layer) if isinstance(value, prof.PerLayer) else value

    @property
    def edit(self):
        return self.c.inspector["edit"]

    def type(self, key, text):
        self.c.setField(key, text)


class EventKindTests(InspectorCase):
    def test_none_to_a_note_on_the_shown_layer(self):
        self.pick("key.5", 2)
        self.c.setAction("event")
        self.assertEqual(self.event("key.5", 2), prof.Note(note=36))
        self.assertIsNone(self.event("key.5", 1))
        self.assertTrue(self.c.dirty)

    def test_note_fields(self):
        self.pick("key.5")
        self.c.setAction("event")
        self.type("note", "60")
        self.type("velocity", "100")
        self.type("mode", "latch")
        self.type("channel", "10")
        self.assertEqual(
            self.event("key.5", 1), prof.Note(note=60, velocity=100, mode="latch", channel=10)
        )
        self.assertEqual(self.edit["noteName"], "C3")
        self.type("channel", "default")
        self.assertIsNone(self.event("key.5", 1).channel)

    def test_the_note_name_hint_goes_blank_while_the_note_field_is_invalid(self):
        self.pick("key.5")
        self.c.setAction("event")
        self.type("note", "60")
        self.assertEqual(self.edit["noteName"], "C3")
        self.type("note", "300")
        self.assertNotEqual(self.edit["fields"]["note"]["error"], "")
        self.assertEqual(self.edit["noteName"], "")
        self.type("note", "61")
        self.assertEqual(self.edit["noteName"], "C#3")

    def test_cc_momentary_fields(self):
        self.pick("key.5")
        self.c.setKind("cc-momentary")
        for key, text in (("cc", "20"), ("low", "10"), ("high", "120"), ("rise-ms", "250"),
                          ("fall-ms", "600"), ("curve", "ease-out"), ("mode", "latch")):
            self.type(key, text)
        self.assertEqual(
            self.event("key.5", 1),
            prof.CcMomentary(cc=20, low=10, high=120, rise_ms=250, fall_ms=600, curve="ease-out", mode="latch"),
        )

    def test_cc_set(self):
        self.pick("key.5")
        self.c.setKind("cc-set")
        self.type("cc", "7")
        self.type("value", "99")
        self.assertEqual(self.event("key.5", 1), prof.CcSet(cc=7, value=99))

    def test_cc_step_stores_a_signed_step(self):
        self.pick("key.5")
        self.c.setKind("cc-step")
        self.type("size", "8")
        self.type("ease-ms", "120")
        self.type("curve", "ease-in-out")
        self.assertEqual(self.event("key.5", 1), prof.CcStep(cc=16, step=8, ease_ms=120, curve="ease-in-out"))
        self.type("direction", "dec")
        self.assertEqual(self.event("key.5", 1).step, -8)
        self.type("size", "3")
        self.assertEqual(self.event("key.5", 1).step, -3)
        self.assertEqual(self.edit["fields"]["direction"]["text"], "dec")

    def test_changing_kind_keeps_cc_and_channel(self):
        self.pick("key.5")
        self.c.setKind("cc-set")
        self.type("cc", "33")
        self.type("channel", "4")
        self.c.setKind("cc-step")
        self.assertEqual(self.event("key.5", 1), prof.CcStep(cc=33, step=1, channel=4))

    def test_turn_kinds(self):
        self.pick("enc.1.turn")
        self.c.setKind("cc-relative")
        self.type("cc", "17")
        self.type("encoding", "binary-offset")
        self.assertEqual(self.event("enc.1.turn", 1), prof.CcRelative(cc=17, encoding="binary-offset"))
        self.c.setKind("cc-absolute")
        self.type("step", "4")
        self.type("initial", "64")
        self.assertEqual(self.event("enc.1.turn", 1), prof.CcAbsolute(cc=17, step=4, initial=64))
        self.type("initial", "")
        self.assertIsNone(self.event("enc.1.turn", 1).initial)

    def test_a_turn_takes_no_layer_action(self):
        self.pick("enc.1.turn")
        self.c.setAction("layer")
        self.c.setLayerKey("layer-inc", 0)
        self.assertNotIn("enc.1.turn", self.c.profile.controls)

    def test_none_clears_the_shown_layer_only(self):
        self.pick("key.2", 1)
        self.c.setAction("none")
        self.assertIsNone(self.event("key.2", 1))
        self.assertEqual(self.event("key.2", 2), prof.CcSet(cc=21, value=64))

    def test_none_on_a_global_event_clears_it_everywhere(self):
        self.pick("key.1", 2)
        self.c.setAction("none")
        self.assertNotIn("key.1", self.c.profile.controls)

    def test_every_edit_updates_the_tile_at_once(self):
        self.pick("key.5")
        self.c.setAction("event")
        self.type("note", "61")
        tile = next(k for k in self.c.keys if k["control"] == "key.5")
        self.assertEqual(tile["line1"], "Note C#3")


class InvalidInputTests(InspectorCase):
    def test_invalid_text_never_reaches_the_profile(self):
        self.pick("key.1")
        before = self.c.profile
        for text in ("300", "", "abc", "-1", "1.5", "0x10"):
            with self.subTest(text=text):
                self.type("note", text)
                self.assertIs(self.c.profile, before)
                self.assertFalse(self.c.dirty)
                field = self.edit["fields"]["note"]
                self.assertEqual(field["text"], text)
                self.assertIn("expected an integer 0..127", field["error"])

    def test_the_error_is_the_profiles_own_message(self):
        self.pick("key.1")
        self.type("note", "300")
        self.assertEqual(self.edit["fields"]["note"]["error"], "expected an integer 0..127, got 300")

    def test_a_valid_entry_clears_the_error(self):
        self.pick("key.1")
        self.type("note", "300")
        self.type("note", "40")
        self.assertEqual(self.edit["fields"]["note"]["error"], "")
        self.assertEqual(self.event("key.1").note, 40)

    def test_a_draft_survives_edits_to_other_fields_but_not_a_new_selection(self):
        self.pick("key.1")
        self.type("note", "300")
        self.type("velocity", "90")
        self.assertEqual(self.edit["fields"]["note"]["text"], "300")
        self.assertEqual(self.event("key.1"), prof.Note(note=36, velocity=90))
        self.c.selectControl("key.2")
        self.c.selectControl("key.1")
        self.assertEqual(self.edit["fields"]["note"]["text"], "36")

    def test_zero_step_size_and_out_of_range_numbers_are_refused(self):
        self.pick("key.5")
        self.c.setKind("cc-step")
        for key, text in (("size", "0"), ("size", "200"), ("ease-ms", "10001"), ("cc", "128")):
            with self.subTest(key=key, text=text):
                self.type(key, text)
                self.assertNotEqual(self.edit["fields"][key]["error"], "")
        self.assertEqual(self.event("key.5", 1), prof.CcStep(cc=16, step=1))

    def test_an_unknown_kind_is_refused(self):
        self.pick("key.1")
        self.c.setKind("layer-inc")
        self.assertEqual(self.event("key.1"), prof.Note(note=36))
        self.assertIn("kind", self.c.error)

    def test_a_cross_control_clash_shows_in_the_problems_list(self):
        self.pick("enc.1.turn")
        self.c.setKind("cc-absolute")
        self.type("cc", "21")
        self.type("initial", "10")
        self.c.selectControl("enc.2.turn")
        self.type("initial", "20")
        self.assertTrue(self.c.problems)
        self.assertFalse(self.c.canSave)


class LayerKeyTests(InspectorCase):
    def test_a_layer_key_replaces_an_empty_control_without_asking(self):
        self.pick("enc.3.push")
        self.c.setAction("layer")
        self.assertEqual(self.event("enc.3.push"), prof.LayerInc())
        self.assertEqual(self.prompts, [])

    def test_layer_key_choices(self):
        self.pick("enc.3.push", 2)
        self.c.setLayerKey("layer-set", 3)
        self.assertEqual(self.event("enc.3.push"), prof.LayerSet(layer=3))
        self.c.setLayerKey("layer-dec", 0)
        self.assertEqual(self.event("enc.3.push"), prof.LayerDec())
        self.c.setLayerKey("layer-set", 0)  # 0: the shown layer
        self.assertEqual(self.event("enc.3.push"), prof.LayerSet(layer=2))
        self.assertEqual(self.prompts, [])

    def test_a_layer_key_is_global_and_shows_locked_on_every_tab(self):
        self.pick("enc.3.push")
        self.c.setLayerKey("layer-inc", 0)
        for tab in range(0, 4):
            self.c.selectTab(tab)
            tile = next(d["push"] for d in self.c.dials if d["push"]["control"] == "enc.3.push")
            self.assertEqual((tile["state"], tile["badge"]), ("layer-key", "🔒"))
            self.assertEqual(self.edit["mode"], "layer-key")

    def test_a_layer_set_past_the_layer_count_is_refused(self):
        self.pick("enc.3.push")
        self.c.setLayerKey("layer-set", 6)
        self.assertNotIn("enc.3.push", self.c.profile.controls)
        self.assertIn("layer", self.c.error)

    def test_making_a_control_with_events_a_layer_key_asks_first(self):
        self.pick("key.2")
        self.c.setAction("layer")
        self.assertEqual(len(self.prompts), 1)
        self.assertIn("Key 2 has its own events on layers 1 and 2", self.prompts[0][1])
        self.assertIsInstance(self.c.profile.controls["key.2"], prof.PerLayer)  # not yet
        self.c.resolveConfirm(True)
        self.assertEqual(self.event("key.2"), prof.LayerInc())

    def test_declining_leaves_the_profile_alone(self):
        self.pick("key.1")
        self.c.setAction("layer")
        self.assertEqual(len(self.prompts), 1)
        self.c.resolveConfirm(False)
        self.assertEqual(self.event("key.1"), prof.Note(note=36))
        self.assertFalse(self.c.dirty)

    def test_a_layer_key_back_to_an_event_goes_on_the_shown_layer(self):
        self.pick("enc.3.push")
        self.c.setLayerKey("layer-inc", 0)
        self.c.selectTab(2)
        self.c.setAction("event")
        self.assertEqual(self.event("enc.3.push", 2), prof.Note(note=36))
        self.assertIsNone(self.event("enc.3.push", 1))
        self.assertEqual(self.prompts, [])

    def test_a_layer_key_on_the_global_tab_becomes_a_global_event(self):
        self.pick("enc.3.push")
        self.c.setLayerKey("layer-inc", 0)
        self.c.selectTab(0)
        self.c.setAction("event")
        self.assertEqual(self.event("enc.3.push"), prof.Note(note=36))

    def test_none_clears_a_layer_key_everywhere(self):
        self.pick("enc.3.push", 2)
        self.c.setLayerKey("layer-inc", 0)
        self.c.setAction("none")
        self.assertNotIn("enc.3.push", self.c.profile.controls)


class GlobalSwitchTests(InspectorCase):
    def test_per_layer_to_global_asks_when_other_layers_differ(self):
        self.pick("key.2", 1)
        self.c.setApplies("global")
        self.assertEqual(len(self.prompts), 1)
        self.assertEqual(
            self.prompts[0][1],
            "Key 2 has its own events on layer 2. Make layer 1's event apply to all layers and discard those?",
        )
        self.c.resolveConfirm(True)
        self.assertEqual(self.c.profile.controls["key.2"], prof.Note(note=37))
        self.assertEqual(self.edit["applies"], "global")

    def test_declining_keeps_the_per_layer_events(self):
        self.pick("key.2", 1)
        self.c.setApplies("global")
        self.c.resolveConfirm(False)
        self.assertIsInstance(self.c.profile.controls["key.2"], prof.PerLayer)
        self.assertFalse(self.c.dirty)

    def test_per_layer_to_global_does_not_ask_when_nothing_is_lost(self):
        self.pick("key.5")
        self.c.setAction("event")
        self.c.setApplies("global")
        self.assertEqual(self.prompts, [])
        self.assertEqual(self.c.profile.controls["key.5"], prof.Note(note=36))

    def test_global_to_per_layer_copies_the_event_to_every_layer(self):
        self.pick("key.1", 2)
        self.c.setApplies("layer")
        control = self.c.profile.controls["key.1"]
        self.assertEqual(control, prof.PerLayer.of({n: prof.Note(note=36) for n in (1, 2, 3)}))
        self.assertEqual(self.prompts, [])
        self.type("note", "50")  # now only the shown layer changes
        self.assertEqual(self.event("key.1", 2).note, 50)
        self.assertEqual(self.event("key.1", 1).note, 36)

    def test_editing_a_global_event_from_any_tab_changes_it_everywhere(self):
        self.pick("key.1", 3)
        self.type("note", "48")
        self.assertEqual(self.c.profile.controls["key.1"], prof.Note(note=48))

    def test_the_global_tab_shows_a_per_layer_control_as_not_editable(self):
        self.pick("key.2", 0)
        self.assertEqual(self.edit["mode"], "each")
        self.c.setField("note", "10")  # nothing to edit here
        self.c.setAction("event")
        self.assertIsInstance(self.c.profile.controls["key.2"], prof.PerLayer)
        self.assertEqual(self.event("key.2", 1), prof.Note(note=37))

    def test_make_global_from_the_global_tab_keeps_the_lowest_layer(self):
        self.pick("key.2", 0)
        self.c.setApplies("global")
        self.assertEqual(len(self.prompts), 1)
        self.assertIn("layer 1's event", self.prompts[0][1])
        self.c.resolveConfirm(True)
        self.assertEqual(self.c.profile.controls["key.2"], prof.Note(note=37))

    def test_a_new_event_on_the_global_tab_is_global(self):
        self.pick("key.5", 0)
        self.c.setAction("event")
        self.assertEqual(self.c.profile.controls["key.5"], prof.Note(note=36))

    def test_the_saved_file_round_trips(self):
        self.pick("key.5")
        self.c.setKind("cc-step")
        self.type("direction", "dec")
        self.type("size", "5")
        self.c.saveProfile()
        saved = prof.load_profile(prof.profile_path("default", self.home))
        self.assertEqual(saved.controls["key.5"], prof.PerLayer.of({1: prof.CcStep(cc=16, step=-5)}))


class ModelTests(InspectorCase):
    def test_nothing_selected_has_no_editor(self):
        self.assertEqual(self.edit["mode"], "none")
        self.assertFalse(self.c.inspector["selected"])

    def test_also_on_lists_the_other_layers(self):
        self.pick("key.2", 1)
        self.assertEqual([a["layer"] for a in self.edit["alsoOn"]], [2, 3])

    def test_slots_ignore_an_empty_selection(self):
        self.c.setAction("event")
        self.c.setKind("note")
        self.c.setField("note", "1")
        self.c.setApplies("global")
        self.c.setLayerKey("layer-inc", 0)
        self.assertFalse(self.c.dirty)


if __name__ == "__main__":
    unittest.main()
