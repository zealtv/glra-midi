# SPDX-License-Identifier: GPL-3.0-only

import unittest

from glra_osc.engine import Engine, describe
from glra_osc.events import ControlEvent
from glra_osc.profile import parse_profile


def ev(control, action, t=0.0):
    return ControlEvent(control, action, t)


def engine(text, **kwargs):
    """An engine for profile TOML (the `version` line is added)."""
    return Engine(parse_profile("version = 1\n" + text), **kwargs)


def one_layer_default():
    """The pre-profile default mapping, as a profile: keys 1..16 are notes 36..51, dial pushes are
    notes 52..54, dial turns are relative CC 16..18; one layer, everything global."""
    parts = ["[layers]\ncount = 1\n"]
    parts += [f'[key.{n}]\nkind = "note"\nnote = {35 + n}\n' for n in range(1, 17)]
    parts += [f'[enc.{n}.push]\nkind = "note"\nnote = {51 + n}\n' for n in (1, 2, 3)]
    parts += [f'[enc.{n}.turn]\nkind = "cc-relative"\ncc = {15 + n}\n' for n in (1, 2, 3)]
    return "".join(parts)


class OneLayerGlobalTests(unittest.TestCase):
    def setUp(self):
        self.e = engine(one_layer_default())

    def test_key_momentary_note(self):
        self.assertEqual(self.e.handle(ev("key.1", "down")), [bytes([0x90, 36, 127])])
        self.assertEqual(self.e.handle(ev("key.1", "up")), [bytes([0x80, 36, 0])])
        self.assertEqual(self.e.held, [])

    def test_repeated_down_and_stray_up_are_ignored(self):
        self.e.handle(ev("key.2", "down"))
        self.assertEqual(self.e.handle(ev("key.2", "down")), [])
        self.e.handle(ev("key.2", "up"))
        self.assertEqual(self.e.handle(ev("key.2", "up")), [])

    def test_encoder_push_and_relative_turn(self):
        self.assertEqual(self.e.handle(ev("enc.2.push", "down")), [bytes([0x90, 53, 127])])
        self.assertEqual(self.e.handle(ev("enc.2", "cw")), [bytes([0xB0, 17, 1])])
        self.assertEqual(self.e.handle(ev("enc.2", "ccw")), [bytes([0xB0, 17, 127])])

    def test_unidentified_unknown_and_wrong_action_events_send_nothing(self):
        for control, action in [
            ("enc.?", "cw"),
            ("enc.?.push", "down"),
            ("key.unknown:0x04", "down"),
            ("consumer.unknown:0x00cd", "down"),
            ("key.1", "cw"),
            ("enc.1", "down"),
            ("key.x", "down"),
        ]:
            self.assertEqual(self.e.handle(ev(control, action)), [], (control, action))

    def test_release_all_sends_note_off_for_everything_held_once(self):
        self.e.handle(ev("key.1", "down"))
        self.e.handle(ev("key.3", "down"))
        self.e.handle(ev("enc.1.push", "down"))
        self.e.handle(ev("key.3", "up"))
        self.assertEqual(
            self.e.release_all(),
            [bytes([0x80, 36, 0]), bytes([0x80, 52, 0])],
        )
        self.assertEqual(self.e.release_all(), [])
        # After release the late physical "up" must not send a second Note Off.
        self.assertEqual(self.e.handle(ev("key.1", "up")), [])


class BindingVariantTests(unittest.TestCase):
    def test_channel_goes_into_the_status_byte(self):
        e = engine('[midi]\nchannel = 10\n[key.1]\nkind = "note"\nnote = 60\nvelocity = 90\n')
        self.assertEqual(e.handle(ev("key.1", "down")), [bytes([0x99, 60, 90])])
        self.assertEqual(e.handle(ev("key.1", "up")), [bytes([0x89, 60, 0])])

    def test_missing_control_is_unmapped(self):
        e = engine('[key.1]\nkind = "note"\nnote = 60\n')
        self.assertEqual(e.handle(ev("key.2", "down")), [])
        self.assertEqual(e.handle(ev("enc.1", "cw")), [])

    def test_momentary_cc_uses_high_and_low_values(self):
        e = engine('[key.1]\nkind = "cc-momentary"\ncc = 64\nlow = 5\nhigh = 100\n')
        self.assertEqual(e.handle(ev("key.1", "down")), [bytes([0xB0, 64, 100])])
        self.assertEqual(e.handle(ev("key.1", "up")), [bytes([0xB0, 64, 5])])

    def test_held_momentary_cc_is_released_on_exit(self):
        e = engine('[key.1]\nkind = "cc-momentary"\ncc = 64\nlow = 5\nhigh = 100\n')
        e.handle(ev("key.1", "down"))
        self.assertEqual(e.release_all(), [bytes([0xB0, 64, 5])])

    def test_latch_note_flips_on_down_and_ignores_up(self):
        e = engine('[key.1]\nkind = "note"\nnote = 60\nmode = "latch"\n')
        self.assertEqual(e.handle(ev("key.1", "down")), [bytes([0x90, 60, 127])])
        self.assertEqual(e.handle(ev("key.1", "up")), [])
        self.assertEqual(e.handle(ev("key.1", "down")), [bytes([0x80, 60, 0])])
        self.assertEqual(e.release_all(), [])

    def test_latch_note_left_on_is_released_and_starts_off_again(self):
        e = engine('[key.1]\nkind = "note"\nnote = 60\nmode = "latch"\n')
        e.handle(ev("key.1", "down"))
        self.assertEqual(e.release_all(), [bytes([0x80, 60, 0])])
        self.assertEqual(e.handle(ev("key.1", "down")), [bytes([0x90, 60, 127])])

    def test_latch_cc_sends_on_off_and_keeps_its_value_on_exit(self):
        e = engine('[key.1]\nkind = "cc-momentary"\ncc = 20\nmode = "latch"\n')
        self.assertEqual(e.handle(ev("key.1", "down")), [bytes([0xB0, 20, 127])])
        self.assertEqual(e.release_all(), [])
        self.assertEqual(e.handle(ev("key.1", "down")), [bytes([0xB0, 20, 0])])


class TurnTests(unittest.TestCase):
    def test_relative_encodings(self):
        expected = {
            "twos-complement": (1, 127),
            "binary-offset": (65, 63),
            "signed-bit": (1, 65),
        }
        for encoding, (cw, ccw) in expected.items():
            e = engine(f'[enc.1.turn]\nkind = "cc-relative"\ncc = 9\nencoding = "{encoding}"\n')
            self.assertEqual(e.handle(ev("enc.1", "cw")), [bytes([0xB0, 9, cw])], encoding)
            self.assertEqual(e.handle(ev("enc.1", "ccw")), [bytes([0xB0, 9, ccw])], encoding)

    def test_absolute_steps_from_initial(self):
        e = engine('[enc.1.turn]\nkind = "cc-absolute"\ncc = 7\ninitial = 10\nstep = 5\n')
        self.assertEqual(e.handle(ev("enc.1", "cw")), [bytes([0xB0, 7, 15])])
        self.assertEqual(e.handle(ev("enc.1", "ccw")), [bytes([0xB0, 7, 10])])

    def test_absolute_clamps_and_stays_quiet_at_the_limits(self):
        e = engine('[enc.1.turn]\nkind = "cc-absolute"\ncc = 7\ninitial = 126\nstep = 5\n')
        self.assertEqual(e.handle(ev("enc.1", "cw")), [bytes([0xB0, 7, 127])])
        self.assertEqual(e.handle(ev("enc.1", "cw")), [])
        e = engine('[enc.1.turn]\nkind = "cc-absolute"\ncc = 7\ninitial = 2\nstep = 5\n')
        self.assertEqual(e.handle(ev("enc.1", "ccw")), [bytes([0xB0, 7, 0])])
        self.assertEqual(e.handle(ev("enc.1", "ccw")), [])

    def test_absolute_state_is_per_encoder(self):
        e = engine(
            '[enc.1.turn]\nkind = "cc-absolute"\ncc = 7\ninitial = 0\n'
            '[enc.2.turn]\nkind = "cc-absolute"\ncc = 8\ninitial = 100\n'
        )
        e.handle(ev("enc.1", "cw"))
        self.assertEqual(e.handle(ev("enc.2", "cw")), [bytes([0xB0, 8, 101])])


pengine = engine


def down_up(e, control):
    return e.handle(ev(control, "down")), e.handle(ev(control, "up"))


class EventKindTests(unittest.TestCase):
    """Each kind, global and on a layer."""

    GLOBAL = {
        "note": '[key.1]\nkind = "note"\nnote = 60\nvelocity = 90\nchannel = 3\n',
        "cc-set": '[key.1]\nkind = "cc-set"\ncc = 20\nvalue = 64\nchannel = 3\n',
        "cc-step": '[key.1]\nkind = "cc-step"\ncc = 20\nstep = 8\nchannel = 3\n',
        "cc-momentary": '[key.1]\nkind = "cc-momentary"\ncc = 20\nlow = 5\nhigh = 100\nchannel = 3\n',
    }
    EXPECTED = {
        "note": ([bytes([0x92, 60, 90])], [bytes([0x82, 60, 0])]),
        "cc-set": ([bytes([0xB2, 20, 64])], []),
        "cc-step": ([bytes([0xB2, 20, 8])], []),
        "cc-momentary": ([bytes([0xB2, 20, 100])], [bytes([0xB2, 20, 5])]),
    }

    def test_global(self):
        for kind, text in self.GLOBAL.items():
            for layer in (1, 2, 3):
                e = pengine("[layers]\ncount = 3\n" + text, layer=layer)
                self.assertEqual(down_up(e, "key.1"), self.EXPECTED[kind], (kind, layer))

    def test_on_a_layer(self):
        for kind, text in self.GLOBAL.items():
            text = text.replace("[key.1]", "[key.1.layers.2]")
            e = pengine("[layers]\ncount = 3\n" + text, layer=2)
            self.assertEqual(down_up(e, "key.1"), self.EXPECTED[kind], kind)

    def test_per_layer_control_does_nothing_where_it_has_no_event(self):
        text = '[layers]\ncount = 3\n[key.1.layers.2]\nkind = "note"\nnote = 60\n'
        for layer in (1, 3):
            e = pengine(text, layer=layer)
            self.assertEqual(down_up(e, "key.1"), ([], []), layer)
        self.assertEqual(down_up(pengine(text, layer=2), "key.1")[0], [bytes([0x90, 60, 127])])

    def test_default_channel_applies_when_an_event_names_none(self):
        e = pengine('[midi]\nchannel = 5\n[key.1]\nkind = "note"\nnote = 60\n')
        self.assertEqual(e.handle(ev("key.1", "down")), [bytes([0x94, 60, 127])])

    def test_turns_global_and_per_layer_use_the_profile_name_enc_n_turn(self):
        e = pengine(
            "[layers]\ncount = 2\n"
            '[enc.1.turn]\nkind = "cc-relative"\ncc = 16\n'
            '[enc.2.turn.layers.2]\nkind = "cc-relative"\ncc = 17\nchannel = 2\n'
        )
        self.assertEqual(e.handle(ev("enc.1", "cw")), [bytes([0xB0, 16, 1])])
        self.assertEqual(e.handle(ev("enc.2", "cw")), [])  # no event on layer 1
        e.handle(ev("enc.3.push", "down"))  # nothing there
        e = pengine(
            "[layers]\ncount = 2\n"
            '[enc.2.turn.layers.2]\nkind = "cc-relative"\ncc = 17\nchannel = 2\n',
            layer=2,
        )
        self.assertEqual(e.handle(ev("enc.2", "ccw")), [bytes([0xB1, 17, 127])])

    def test_latch_cc_toggles_between_high_and_low(self):
        e = pengine('[key.1]\nkind = "cc-momentary"\ncc = 20\nlow = 10\nhigh = 90\nmode = "latch"\n')
        self.assertEqual(e.handle(ev("key.1", "down")), [bytes([0xB0, 20, 90])])
        self.assertEqual(e.handle(ev("key.1", "up")), [])
        self.assertEqual(e.handle(ev("key.1", "down")), [bytes([0xB0, 20, 10])])


LAYERS = """
[layers]
count = 3

[key.1]
kind = "layer-inc"

[key.2]
kind = "layer-dec"

[key.3]
kind = "layer-set"
layer = 3

[enc.1.push]
kind = "layer-set"
layer = 1

[key.5.layers.1]
kind = "note"
note = 60

[key.5.layers.2]
kind = "note"
note = 61

[key.6.layers.1]
kind = "note"
note = 70
mode = "latch"

[key.6.layers.2]
kind = "note"
note = 71
mode = "latch"

[key.7]
kind = "note"
note = 80
"""


class LayerTests(unittest.TestCase):
    def setUp(self):
        self.changes = []
        self.e = pengine(LAYERS, on_layer=lambda old, new: self.changes.append((old, new)))

    def tap(self, control):
        return down_up(self.e, control)

    def test_layer_keys_act_on_press_send_nothing_and_work_from_every_layer(self):
        self.assertEqual(self.e.layer, 1)
        self.assertEqual(self.e.handle(ev("key.1", "down")), [])
        self.assertEqual(self.e.layer, 2)
        self.assertEqual(self.e.handle(ev("key.1", "up")), [])
        self.assertEqual(self.e.layer, 2)
        self.tap("key.3")
        self.assertEqual(self.e.layer, 3)
        self.tap("enc.1.push")
        self.assertEqual(self.e.layer, 1)
        self.assertEqual(self.changes, [(1, 2), (2, 3), (3, 1)])

    def test_inc_and_dec_wrap(self):
        self.tap("key.2")
        self.assertEqual(self.e.layer, 3)  # 1 - 1 wraps to the last
        self.tap("key.1")
        self.assertEqual(self.e.layer, 1)  # last + 1 wraps to 1
        self.assertEqual(self.changes, [(1, 3), (3, 1)])

    def test_setting_the_current_layer_is_no_change(self):
        self.tap("enc.1.push")
        self.assertEqual((self.e.layer, self.changes), (1, []))

    def test_single_layer_inc_and_dec_do_nothing(self):
        e = pengine('[layers]\ncount = 1\n[key.1]\nkind = "layer-inc"\n[key.2]\nkind = "layer-dec"\n')
        self.assertEqual((down_up(e, "key.1"), down_up(e, "key.2"), e.layer), (([], []), ([], []), 1))

    def test_layer_changes_what_a_per_layer_key_does(self):
        self.assertEqual(self.e.handle(ev("key.5", "down")), [bytes([0x90, 60, 127])])
        self.e.handle(ev("key.5", "up"))
        self.tap("key.1")
        self.assertEqual(self.e.handle(ev("key.5", "down")), [bytes([0x90, 61, 127])])

    def test_global_control_is_the_same_on_every_layer(self):
        for _ in range(3):
            self.assertEqual(self.tap("key.7"), ([bytes([0x90, 80, 127])], [bytes([0x80, 80, 0])]))
            self.tap("key.1")

    def test_no_fall_through_from_a_layer_to_a_global_event(self):
        self.tap("key.3")  # layer 3: key.5 has no event there, and nothing stands in
        self.assertEqual(self.tap("key.5"), ([], []))

    def test_release_goes_to_the_binding_the_press_started_with(self):
        self.assertEqual(self.e.handle(ev("key.5", "down")), [bytes([0x90, 60, 127])])
        self.tap("key.1")  # layer 2, where key.5 is note 61
        self.assertEqual(self.e.handle(ev("key.5", "up")), [bytes([0x80, 60, 0])])
        self.assertEqual(self.e.held, [])

    def test_layer_key_with_other_keys_held_leaves_them_alone(self):
        self.e.handle(ev("key.7", "down"))
        self.tap("key.1")
        self.assertEqual(self.e.held, ["key.7"])
        self.assertEqual(self.e.handle(ev("key.7", "up")), [bytes([0x80, 80, 0])])

    def latch(self):
        """Press and release key.6, returning what the press sent."""
        sent = self.e.handle(ev("key.6", "down"))
        self.e.handle(ev("key.6", "up"))
        return sent

    def test_latch_state_is_per_layer_and_a_layer_change_sends_nothing(self):
        self.assertEqual(self.latch(), [bytes([0x90, 70, 127])])
        self.assertEqual(self.tap("key.1"), ([], []))  # to layer 2: nothing turns off
        self.assertEqual(self.latch(), [bytes([0x90, 71, 127])])
        self.tap("key.2")  # back to layer 1: its note is still on
        self.assertEqual(self.latch(), [bytes([0x80, 70, 0])])
        self.tap("key.1")
        self.assertEqual(self.latch(), [bytes([0x80, 71, 0])])

    def test_release_all_turns_off_latched_notes_on_every_layer_and_resets_them(self):
        self.latch()
        self.tap("key.1")
        self.latch()
        self.assertEqual(self.e.release_all(), [bytes([0x80, 70, 0]), bytes([0x80, 71, 0])])
        self.assertEqual(self.latch(), [bytes([0x90, 71, 127])])

    def test_starting_layer(self):
        self.assertEqual(pengine(LAYERS, layer=2).layer, 2)
        self.assertEqual(pengine(LAYERS, layer=9).layer, 1)

    def test_layer_set_beyond_the_count_is_ignored(self):
        from dataclasses import replace

        from glra_osc.profile import LayerSet

        profile = parse_profile("version = 1\n" + LAYERS)
        controls = dict(profile.controls, **{"key.3": LayerSet(9)})
        e = Engine(replace(profile, controls=controls))
        down_up(e, "key.3")
        self.assertEqual(e.layer, 1)


SHARED = """
[key.1]
kind = "cc-set"
cc = 21
value = 64

[key.2]
kind = "cc-step"
cc = 21
step = 8

[key.3]
kind = "cc-step"
cc = 21
step = -8

[key.4]
kind = "cc-step"
cc = 21
step = 100

[key.5]
kind = "cc-momentary"
cc = 21
low = 3
high = 90

[enc.2.turn]
kind = "cc-absolute"
cc = 21
step = 2
initial = 10
"""


class SharedCcValueTests(unittest.TestCase):
    def setUp(self):
        self.e = pengine(SHARED)

    def cc(self, value):
        return [bytes([0xB0, 21, value])]

    def test_value_starts_at_the_dials_initial(self):
        self.assertEqual(self.e.cc_value(1, 21), 10)
        self.assertEqual(self.e.handle(ev("key.2", "down")), self.cc(18))

    def test_set_step_and_dial_share_one_value(self):
        self.assertEqual(self.e.handle(ev("enc.2", "cw")), self.cc(12))
        self.assertEqual(self.e.handle(ev("key.2", "down")), self.cc(20))
        self.assertEqual(self.e.handle(ev("key.1", "down")), self.cc(64))
        self.assertEqual(self.e.handle(ev("enc.2", "ccw")), self.cc(62))
        self.assertEqual(self.e.handle(ev("key.3", "down")), self.cc(54))
        self.assertEqual(self.e.cc_value(1, 21), 54)

    def test_cc_set_always_sends_even_when_unchanged(self):
        self.e.handle(ev("key.1", "down"))
        self.e.handle(ev("key.1", "up"))
        self.assertEqual(self.e.handle(ev("key.1", "down")), self.cc(64))

    def test_step_clamps_and_is_quiet_at_the_clamp(self):
        self.assertEqual(self.e.handle(ev("key.4", "down")), self.cc(110))
        self.e.handle(ev("key.4", "up"))
        self.assertEqual(self.e.handle(ev("key.4", "down")), self.cc(127))
        self.e.handle(ev("key.4", "up"))
        self.assertEqual(self.e.handle(ev("key.4", "down")), [])

    def test_momentary_cc_moves_the_value_and_the_dial_continues_from_it(self):
        self.e.handle(ev("key.5", "down"))
        self.assertEqual(self.e.cc_value(1, 21), 90)
        self.assertEqual(self.e.handle(ev("key.5", "up")), self.cc(3))
        self.assertEqual(self.e.handle(ev("enc.2", "cw")), self.cc(5))

    def test_the_same_cc_on_another_channel_is_separate(self):
        e = pengine(
            '[key.1]\nkind = "cc-set"\ncc = 21\nvalue = 64\n'
            '[key.2]\nkind = "cc-step"\ncc = 21\nstep = 1\nchannel = 2\n'
        )
        e.handle(ev("key.1", "down"))
        self.assertEqual(e.handle(ev("key.2", "down")), [bytes([0xB1, 21, 1])])

    def test_value_table_survives_release_all(self):
        self.e.handle(ev("key.1", "down"))
        self.e.release_all()
        self.assertEqual(self.e.cc_value(1, 21), 64)
        self.assertEqual(self.e.handle(ev("key.2", "down")), self.cc(72))

    def test_release_all_sends_low_for_a_held_momentary_cc_only(self):
        self.e.handle(ev("key.5", "down"))
        self.e.handle(ev("key.1", "down"))
        self.assertEqual(self.e.release_all(), self.cc(3))
        self.assertEqual(self.e.handle(ev("key.5", "up")), [])


class DescribeTests(unittest.TestCase):
    def test_describe(self):
        self.assertEqual(describe(bytes([0x90, 36, 127])), "90 24 7f  ch 1  note on  36  vel 127")
        self.assertEqual(describe(bytes([0xB1, 17, 127])), "b1 11 7f  ch 2  cc       17  value 127")


if __name__ == "__main__":
    unittest.main()
