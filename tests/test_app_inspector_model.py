# SPDX-License-Identifier: GPL-3.0-only

"""The inspector's pure model (`glra_osc/app/inspector.py`): no Qt needed."""

import unittest

from glra_osc import profile as prof
from glra_osc.app import inspector as insp


def profile_with(**controls):
    return prof.Profile(layer_count=3, layer_names=("", "", ""), controls=controls)


class DefaultEventTests(unittest.TestCase):
    def test_every_kind_has_a_valid_default(self):
        for kind in [k for k, _ in insp.PRESS_KINDS + insp.TURN_KINDS]:
            with self.subTest(kind=kind):
                event = insp.default_event(kind)
                self.assertEqual(event.kind, kind)
                self.assertEqual(prof.event_from_fields(kind, prof.event_fields(event)), event)

    def test_a_new_kind_keeps_cc_and_channel(self):
        before = prof.CcSet(cc=21, value=5, channel=7)
        self.assertEqual(insp.default_event("cc-step", before), prof.CcStep(cc=21, step=1, channel=7))
        self.assertEqual(insp.default_event("note", before), prof.Note(note=36, channel=7))

    def test_not_a_kind(self):
        with self.assertRaises(prof.ProfileError):
            insp.default_event("layer-inc")


class ApplyFieldTests(unittest.TestCase):
    def test_a_number_is_parsed_and_checked_by_the_profiles_rules(self):
        note = prof.Note(note=36)
        self.assertEqual(insp.apply_field(note, "note", " 60 "), prof.Note(note=60))
        for text, part in (("300", "0..127"), ("", "0..127"), ("abc", "'abc'"), ("1.5", "'1.5'")):
            with self.subTest(text=text):
                with self.assertRaises(prof.ProfileError) as ctx:
                    insp.apply_field(note, "note", text)
                self.assertIn("expected an integer", str(ctx.exception))
                self.assertIn(part, str(ctx.exception))
                self.assertNotIn("x.note", str(ctx.exception))  # the path is dropped

    def test_the_message_is_the_parsers_own(self):
        with self.assertRaises(prof.ProfileError) as ctx:
            insp.apply_field(prof.CcSet(cc=1, value=2), "cc", "128")
        with self.assertRaises(prof.ProfileError) as parsed:
            prof.parse_profile('version = 1\n[key.1]\nkind = "cc-set"\ncc = 128\nvalue = 2\n')
        self.assertEqual(str(parsed.exception).rpartition(": ")[2], str(ctx.exception))

    def test_channel_default_and_numbers(self):
        note = prof.Note(note=36, channel=5)
        self.assertIsNone(insp.apply_field(note, "channel", "default").channel)
        self.assertEqual(insp.apply_field(note, "channel", "16").channel, 16)
        with self.assertRaises(prof.ProfileError):
            insp.apply_field(note, "channel", "17")

    def test_optional_initial_may_be_emptied(self):
        absolute = prof.CcAbsolute(cc=1, initial=64)
        self.assertIsNone(insp.apply_field(absolute, "initial", "").initial)

    def test_choices_are_checked(self):
        note = prof.Note(note=36)
        self.assertEqual(insp.apply_field(note, "mode", "latch").mode, "latch")
        with self.assertRaises(prof.ProfileError):
            insp.apply_field(note, "mode", "sticky")

    def test_cc_step_direction_and_size_are_the_two_halves_of_step(self):
        step = prof.CcStep(cc=1, step=8)
        self.assertEqual(insp.apply_field(step, "direction", "dec").step, -8)
        self.assertEqual(insp.apply_field(prof.CcStep(cc=1, step=-8), "size", "3").step, -3)
        self.assertEqual(insp.apply_field(step, "size", "3").step, 3)
        for bad in ("0", "128", "x", ""):
            with self.subTest(size=bad), self.assertRaises(prof.ProfileError):
                insp.apply_field(step, "size", bad)

    def test_unknown_field(self):
        with self.assertRaises(prof.ProfileError):
            insp.apply_field(prof.Note(note=36), "cc", "1")


class DescribeTests(unittest.TestCase):
    def test_an_empty_control(self):
        d = insp.describe(profile_with(), "key.1", 1)
        self.assertEqual((d["mode"], d["action"], d["fields"]), ("none", "none", {}))

    def test_a_per_layer_note_lists_the_other_layers(self):
        p = profile_with(
            **{"key.2": prof.PerLayer.of({1: prof.Note(note=37), 2: prof.CcSet(cc=21, value=64)})}
        )
        d = insp.describe(p, "key.2", 1)
        self.assertEqual((d["mode"], d["action"], d["kind"], d["applies"]), ("event", "event", "note", "layer"))
        self.assertEqual(d["noteName"], "C#1")
        self.assertEqual(d["fields"]["note"]["text"], "37")
        self.assertEqual(
            [(a["layer"], a["text"]) for a in d["alsoOn"]], [(2, "L2 CC21 = 64"), (3, "L3 —")]
        )

    def test_a_global_event_is_global_on_every_tab(self):
        p = profile_with(**{"key.1": prof.Note(note=36)})
        for tab in (None, 1, 3):
            d = insp.describe(p, "key.1", tab)
            self.assertEqual((d["mode"], d["applies"], d["alsoOn"]), ("event", "global", []))

    def test_a_per_layer_control_on_the_global_tab_offers_nothing_to_edit(self):
        p = profile_with(**{"key.2": prof.PerLayer.of({1: prof.Note(note=1), 3: prof.Note(note=2)})})
        d = insp.describe(p, "key.2", None)
        self.assertEqual((d["mode"], d["fields"]), ("each", {}))
        self.assertEqual(d["layersUsed"], "Layers 1 and 3")

    def test_a_layer_key_is_a_layer_key_on_every_tab(self):
        p = profile_with(**{"enc.1.push": prof.LayerSet(layer=2)})
        for tab in (None, 1, 2, 3):
            d = insp.describe(p, "enc.1.push", tab)
            self.assertEqual((d["mode"], d["action"]), ("layer-key", "layer"))
            self.assertEqual(d["layerKey"], {"kind": "layer-set", "layer": 2})

    def test_cc_step_shows_direction_and_size(self):
        p = profile_with(**{"key.1": prof.CcStep(cc=5, step=-8, ease_ms=120)})
        f = insp.describe(p, "key.1", 1)["fields"]
        self.assertEqual((f["direction"]["text"], f["size"]["text"]), ("dec", "8"))
        self.assertNotIn("step", f)

    def test_channel_text(self):
        p = profile_with(**{"key.1": prof.Note(note=1, channel=None), "key.2": prof.Note(note=1, channel=4)})
        self.assertEqual(insp.describe(p, "key.1", 1)["fields"]["channel"]["text"], "default")
        self.assertEqual(insp.describe(p, "key.2", 1)["fields"]["channel"]["text"], "4")

    def test_a_draft_replaces_the_text_and_carries_its_error(self):
        p = profile_with(**{"key.1": prof.Note(note=36)})
        d = insp.describe(p, "key.1", 1, {"note": ("300", "expected an integer 0..127, got 300")})
        self.assertEqual(d["fields"]["note"]["text"], "300")
        self.assertIn("0..127", d["fields"]["note"]["error"])

    def test_turn_actions_are_the_turn_kinds(self):
        d = insp.describe(profile_with(**{"enc.1.turn": prof.CcRelative(cc=16)}), "enc.1.turn", 1)
        self.assertEqual(d["action"], "cc-relative")
        self.assertEqual([a["value"] for a in d["actions"]], ["cc-relative", "cc-absolute"])


class DiscardTextTests(unittest.TestCase):
    def test_names_the_layers(self):
        d = [prof.Discarded("key.2", 2, None), prof.Discarded("key.2", 3, None)]
        self.assertEqual(
            insp.discard_text("Key 2", d, kept_layer=1),
            "Key 2 has its own events on layers 2 and 3. "
            "Make layer 1's event apply to all layers and discard those?",
        )

    def test_one_layer_and_a_global_event(self):
        self.assertIn("on layer 2.", insp.discard_text("Key 2", [prof.Discarded("key.2", 2, None)]))
        self.assertIn("every layer", insp.discard_text("Key 2", [prof.Discarded("key.2", None, None)]))


if __name__ == "__main__":
    unittest.main()
