# SPDX-License-Identifier: GPL-3.0-only

import unittest

from glra_osc.engine import Engine, describe
from glra_osc.events import ControlEvent
from glra_osc.mapping import load_mapping, parse_mapping


def ev(control, action, t=0.0):
    return ControlEvent(control, action, t)


def engine(text):
    return Engine(parse_mapping(text))


class DefaultMappingTests(unittest.TestCase):
    def setUp(self):
        self.e = Engine(load_mapping())

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
        e = engine("[global]\nchannel = 10\n[key.1]\nnote = 60\nvelocity = 90\n")
        self.assertEqual(e.handle(ev("key.1", "down")), [bytes([0x99, 60, 90])])
        self.assertEqual(e.handle(ev("key.1", "up")), [bytes([0x89, 60, 0])])

    def test_missing_control_is_unmapped(self):
        e = engine("[key.1]\nnote = 60\n")
        self.assertEqual(e.handle(ev("key.2", "down")), [])
        self.assertEqual(e.handle(ev("enc.1", "cw")), [])

    def test_momentary_cc_uses_on_and_off_values(self):
        e = engine("[key.1]\ncc = 64\non = 100\noff = 5\n")
        self.assertEqual(e.handle(ev("key.1", "down")), [bytes([0xB0, 64, 100])])
        self.assertEqual(e.handle(ev("key.1", "up")), [bytes([0xB0, 64, 5])])

    def test_held_momentary_cc_is_released_on_exit(self):
        e = engine("[key.1]\ncc = 64\non = 100\noff = 5\n")
        e.handle(ev("key.1", "down"))
        self.assertEqual(e.release_all(), [bytes([0xB0, 64, 5])])

    def test_toggle_note_flips_on_down_and_ignores_up(self):
        e = engine('[key.1]\nnote = 60\nmode = "toggle"\n')
        self.assertEqual(e.handle(ev("key.1", "down")), [bytes([0x90, 60, 127])])
        self.assertEqual(e.handle(ev("key.1", "up")), [])
        self.assertEqual(e.handle(ev("key.1", "down")), [bytes([0x80, 60, 0])])
        self.assertEqual(e.release_all(), [])

    def test_toggle_note_left_on_is_released_and_starts_off_again(self):
        e = engine('[key.1]\nnote = 60\nmode = "toggle"\n')
        e.handle(ev("key.1", "down"))
        self.assertEqual(e.release_all(), [bytes([0x80, 60, 0])])
        self.assertEqual(e.handle(ev("key.1", "down")), [bytes([0x90, 60, 127])])

    def test_toggle_cc_sends_on_off_and_keeps_its_value_on_exit(self):
        e = engine('[key.1]\ncc = 20\nmode = "toggle"\n')
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
            e = engine(f'[enc.1.turn]\ntype = "relative"\ncc = 9\nencoding = "{encoding}"\n')
            self.assertEqual(e.handle(ev("enc.1", "cw")), [bytes([0xB0, 9, cw])], encoding)
            self.assertEqual(e.handle(ev("enc.1", "ccw")), [bytes([0xB0, 9, ccw])], encoding)

    def test_absolute_steps_from_initial(self):
        e = engine('[enc.1.turn]\ntype = "absolute"\ncc = 7\ninitial = 10\nstep = 5\n')
        self.assertEqual(e.handle(ev("enc.1", "cw")), [bytes([0xB0, 7, 15])])
        self.assertEqual(e.handle(ev("enc.1", "ccw")), [bytes([0xB0, 7, 10])])

    def test_absolute_clamps_and_stays_quiet_at_the_limits(self):
        e = engine('[enc.1.turn]\ntype = "absolute"\ncc = 7\ninitial = 126\nstep = 5\n')
        self.assertEqual(e.handle(ev("enc.1", "cw")), [bytes([0xB0, 7, 127])])
        self.assertEqual(e.handle(ev("enc.1", "cw")), [])
        e = engine('[enc.1.turn]\ntype = "absolute"\ncc = 7\ninitial = 2\nstep = 5\n')
        self.assertEqual(e.handle(ev("enc.1", "ccw")), [bytes([0xB0, 7, 0])])
        self.assertEqual(e.handle(ev("enc.1", "ccw")), [])

    def test_absolute_state_is_per_encoder(self):
        e = engine(
            '[enc.1.turn]\ntype = "absolute"\ncc = 7\ninitial = 0\n'
            '[enc.2.turn]\ntype = "absolute"\ncc = 8\ninitial = 100\n'
        )
        e.handle(ev("enc.1", "cw"))
        self.assertEqual(e.handle(ev("enc.2", "cw")), [bytes([0xB0, 8, 101])])


class DescribeTests(unittest.TestCase):
    def test_describe(self):
        self.assertEqual(describe(bytes([0x90, 36, 127])), "90 24 7f  ch 1  note on  36  vel 127")
        self.assertEqual(describe(bytes([0xB1, 17, 127])), "b1 11 7f  ch 2  cc       17  value 127")


if __name__ == "__main__":
    unittest.main()
