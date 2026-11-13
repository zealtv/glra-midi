# SPDX-License-Identifier: GPL-3.0-only

"""Glides (docs/config-app.md 3.6) on a fake clock: nothing sleeps."""

import unittest

from glra_midi.engine import Engine
from glra_midi.events import ControlEvent
from glra_midi.profile import parse_profile


def ev(control, action, t=0.0):
    return ControlEvent(control, action, t)


def engine(text):
    return Engine(parse_profile("version = 1\n[layers]\ncount = 2\n" + text))


def cc(channel, number, value):
    return bytes([0xB0 | (channel - 1), number, value])


def run(e, start, end, step=0.01):
    """Tick at start+step, start+2*step, ... up to `end`; the (time, message) pairs sent."""
    sent = []
    k = 1
    while round(start + k * step, 9) <= end:
        now = round(start + k * step, 9)
        sent += [(now, m) for m in e.tick(now)]
        k += 1
    return sent


def values(sent):
    return [m[2] for _, m in sent]


def momentary(rise=100, fall=0, curve="linear", low=0, high=100, extra=""):
    return (
        f'[key.1]\nkind = "cc-momentary"\ncc = 20\nlow = {low}\nhigh = {high}\n'
        f'rise-ms = {rise}\nfall-ms = {fall}\ncurve = "{curve}"\n{extra}'
    )


class CurveTests(unittest.TestCase):
    """0 -> 100 over 100 ms, ticked every 10 ms: the exact sequence for each curve."""

    def sequence(self, curve):
        e = engine(momentary(curve=curve))
        self.assertEqual(e.handle(ev("key.1", "down", 0.0)), [])  # progress 0 equals the start
        return values(run(e, 0.0, 0.2))

    def test_linear(self):
        self.assertEqual(self.sequence("linear"), [10, 20, 30, 40, 50, 60, 70, 80, 90, 100])

    def test_ease_in(self):
        self.assertEqual(self.sequence("ease-in"), [1, 4, 9, 16, 25, 36, 49, 64, 81, 100])

    def test_ease_out(self):
        self.assertEqual(self.sequence("ease-out"), [19, 36, 51, 64, 75, 84, 91, 96, 99, 100])

    def test_ease_in_out(self):
        self.assertEqual(self.sequence("ease-in-out"), [2, 8, 18, 32, 50, 68, 82, 92, 98, 100])

    def test_a_falling_glide_runs_the_curve_downward(self):
        e = engine(momentary(rise=0, fall=100, curve="ease-in", low=0, high=100))
        e.handle(ev("key.1", "down", 0.0))
        e.handle(ev("key.1", "up", 1.0))
        self.assertEqual(values(run(e, 1.0, 1.2)), [99, 96, 91, 84, 75, 64, 51, 36, 19, 0])


class TimingTests(unittest.TestCase):
    def test_ends_exactly_on_the_target_and_then_goes_idle(self):
        e = engine(momentary(rise=100))
        e.handle(ev("key.1", "down", 0.0))
        self.assertEqual(e.next_due(), 0.01)
        sent = run(e, 0.0, 0.2)
        self.assertEqual(sent[-1], (0.1, cc(1, 20, 100)))
        self.assertEqual(e.cc_value(1, 20), 100)
        self.assertIsNone(e.next_due())
        self.assertEqual(e.tick(0.3), [])

    def test_next_due_follows_the_tick(self):
        e = engine(momentary(rise=100))
        self.assertIsNone(e.next_due())
        e.handle(ev("key.1", "down", 5.0))
        self.assertEqual(e.next_due(), 5.01)
        e.tick(5.01)
        self.assertEqual(e.next_due(), 5.02)

    def test_a_late_tick_catches_up_in_one_message(self):
        e = engine(momentary(rise=100))
        e.handle(ev("key.1", "down", 0.0))
        self.assertEqual(e.tick(0.05), [cc(1, 20, 50)])
        self.assertEqual(e.tick(0.5), [cc(1, 20, 100)])

    def test_no_duplicate_values(self):
        e = engine(momentary(rise=100, high=3))
        e.handle(ev("key.1", "down", 0.0))
        sent = values(run(e, 0.0, 0.2))
        self.assertEqual(sent, [1, 2, 3])

    def test_zero_ms_jumps_from_handle(self):
        e = engine(momentary(rise=0, fall=0))
        self.assertEqual(e.handle(ev("key.1", "down", 0.0)), [cc(1, 20, 100)])
        self.assertEqual(e.handle(ev("key.1", "up", 0.1)), [cc(1, 20, 0)])
        self.assertIsNone(e.next_due())

    def test_rise_zero_jumps_up_and_fall_glides_down(self):
        e = engine(momentary(rise=0, fall=100))
        self.assertEqual(e.handle(ev("key.1", "down", 0.0)), [cc(1, 20, 100)])
        self.assertEqual(e.handle(ev("key.1", "up", 1.0)), [])
        self.assertEqual(values(run(e, 1.0, 1.2)), [90, 80, 70, 60, 50, 40, 30, 20, 10, 0])

    def test_rise_and_fall_take_their_own_time(self):
        e = engine(momentary(rise=100, fall=200))
        e.handle(ev("key.1", "down", 0.0))
        run(e, 0.0, 0.1)
        e.handle(ev("key.1", "up", 1.0))
        sent = run(e, 1.0, 1.3)
        self.assertEqual(len(sent), 20)
        self.assertEqual(sent[-1], (1.2, cc(1, 20, 0)))

    def test_channel_goes_into_the_status_byte(self):
        e = engine(momentary(extra="channel = 3\n"))
        e.handle(ev("key.1", "down", 0.0))
        self.assertEqual(e.tick(0.01), [cc(3, 20, 10)])


class RetargetTests(unittest.TestCase):
    def test_release_mid_rise_falls_from_where_the_value_is(self):
        e = engine(momentary(rise=100, fall=100))
        e.handle(ev("key.1", "down", 0.0))
        run(e, 0.0, 0.04)  # value 40
        self.assertEqual(e.cc_value(1, 20), 40)
        self.assertEqual(e.handle(ev("key.1", "up", 0.04)), [])
        # full fall time again, from 40 down to 0
        self.assertEqual(values(run(e, 0.04, 0.2)), [36, 32, 28, 24, 20, 16, 12, 8, 4, 0])

    def test_press_mid_fall_rises_from_the_current_value(self):
        e = engine(momentary(rise=100, fall=100))
        e.handle(ev("key.1", "down", 0.0))
        run(e, 0.0, 0.2)
        e.handle(ev("key.1", "up", 1.0))
        run(e, 1.0, 1.05)  # 50
        e.handle(ev("key.1", "down", 1.05))
        self.assertEqual(values(run(e, 1.05, 1.2))[-1], 100)
        self.assertEqual(e.cc_value(1, 20), 100)

    def test_latch_toggles_the_target(self):
        e = engine(momentary(rise=100, fall=100, extra='mode = "latch"\n'))
        e.handle(ev("key.1", "down", 0.0))
        e.handle(ev("key.1", "up", 0.01))  # a latch ignores the release
        self.assertEqual(values(run(e, 0.0, 0.2))[-1], 100)
        e.handle(ev("key.1", "down", 1.0))
        self.assertEqual(values(run(e, 1.0, 1.2))[-1], 0)

    def test_step_presses_build_on_the_old_target(self):
        e = engine('[key.1]\nkind = "cc-step"\ncc = 21\nstep = 8\nease-ms = 100\n')
        for t in (0.0, 0.01, 0.02):
            self.assertEqual(e.handle(ev("key.1", "down", t)), [])
            e.handle(ev("key.1", "up", t + 0.005))
        self.assertEqual(values(run(e, 0.02, 0.2))[-1], 24)

    def test_step_retarget_starts_from_the_value_sent(self):
        e = engine('[key.1]\nkind = "cc-step"\ncc = 21\nstep = 40\nease-ms = 100\n')
        e.handle(ev("key.1", "down", 0.0))
        run(e, 0.0, 0.05)  # 20 of 40
        self.assertEqual(e.cc_value(1, 21), 20)
        e.handle(ev("key.1", "up", 0.05))
        e.handle(ev("key.1", "down", 0.05))  # target 80, from 20, over the full 100 ms
        sent = run(e, 0.05, 0.2)
        self.assertEqual(values(sent), [26, 32, 38, 44, 50, 56, 62, 68, 74, 80])

    def test_step_dec_and_clamps(self):
        e = engine('[key.1]\nkind = "cc-step"\ncc = 21\nstep = -100\nease-ms = 50\n')
        self.assertEqual(e.handle(ev("key.1", "down", 0.0)), [])  # already 0: nothing to do
        self.assertIsNone(e.next_due())
        e = engine(
            '[key.1]\nkind = "cc-step"\ncc = 21\nstep = 100\nease-ms = 50\n'
            '[key.2]\nkind = "cc-step"\ncc = 21\nstep = 100\nease-ms = 50\n'
        )
        e.handle(ev("key.1", "down", 0.0))
        e.handle(ev("key.2", "down", 0.0))  # 100 + 100 clamps at 127
        self.assertEqual(values(run(e, 0.0, 0.1))[-1], 127)

    def test_step_at_zero_ms_jumps_and_only_on_change(self):
        e = engine('[key.1]\nkind = "cc-step"\ncc = 21\nstep = 100\n')
        self.assertEqual(e.handle(ev("key.1", "down", 0.0)), [cc(1, 21, 100)])
        e.handle(ev("key.1", "up", 0.1))
        self.assertEqual(e.handle(ev("key.1", "down", 0.2)), [cc(1, 21, 127)])
        e.handle(ev("key.1", "up", 0.3))
        self.assertEqual(e.handle(ev("key.1", "down", 0.4)), [])

    def test_step_jump_cancels_a_running_glide(self):
        e = engine(
            '[key.1]\nkind = "cc-step"\ncc = 21\nstep = 40\nease-ms = 100\n'
            '[key.2]\nkind = "cc-step"\ncc = 21\nstep = 10\n'
        )
        e.handle(ev("key.1", "down", 0.0))
        run(e, 0.0, 0.05)  # at 20, glide to 40
        self.assertEqual(e.handle(ev("key.2", "down", 0.05)), [cc(1, 21, 50)])  # 40 + 10
        self.assertIsNone(e.next_due())
        self.assertEqual(run(e, 0.05, 0.3), [])


class CancelTests(unittest.TestCase):
    def test_cc_set_cancels_and_wins(self):
        e = engine(momentary(rise=100) + '[key.2]\nkind = "cc-set"\ncc = 20\nvalue = 7\n')
        e.handle(ev("key.1", "down", 0.0))
        run(e, 0.0, 0.03)
        self.assertEqual(e.handle(ev("key.2", "down", 0.03)), [cc(1, 20, 7)])
        self.assertIsNone(e.next_due())
        self.assertEqual(run(e, 0.03, 0.3), [])
        self.assertEqual(e.cc_value(1, 20), 7)

    def test_absolute_dial_cancels_and_wins(self):
        e = engine(
            momentary(rise=100)
            + '[enc.1.turn]\nkind = "cc-absolute"\ncc = 20\nstep = 5\n'
        )
        e.handle(ev("key.1", "down", 0.0))
        run(e, 0.0, 0.03)  # 30
        self.assertEqual(e.handle(ev("enc.1", "cw", 0.03)), [cc(1, 20, 35)])
        self.assertEqual(run(e, 0.03, 0.3), [])

    def test_a_later_glide_replaces_an_earlier_one(self):
        e = engine(
            momentary(rise=100)
            + '[key.2]\nkind = "cc-momentary"\ncc = 20\nlow = 0\nhigh = 10\nrise-ms = 100\n'
        )
        e.handle(ev("key.1", "down", 0.0))
        e.handle(ev("key.2", "down", 0.0))
        self.assertEqual(values(run(e, 0.0, 0.2))[-1], 10)

    def test_glides_on_different_ccs_run_together(self):
        e = engine(
            momentary(rise=100)
            + '[key.2]\nkind = "cc-momentary"\ncc = 21\nhigh = 50\nrise-ms = 100\n'
        )
        e.handle(ev("key.1", "down", 0.0))
        e.handle(ev("key.2", "down", 0.0))
        self.assertEqual(e.tick(0.01), [cc(1, 20, 10), cc(1, 21, 5)])

    def test_same_cc_on_another_channel_is_independent(self):
        e = engine(
            momentary(rise=100)
            + '[key.2]\nkind = "cc-momentary"\ncc = 20\nhigh = 50\nrise-ms = 100\nchannel = 2\n'
        )
        e.handle(ev("key.1", "down", 0.0))
        e.handle(ev("key.2", "down", 0.0))
        self.assertEqual(e.tick(0.01), [cc(1, 20, 10), cc(2, 20, 5)])


class LayerAndReleaseTests(unittest.TestCase):
    def test_a_layer_change_leaves_a_glide_alone(self):
        e = engine(momentary(rise=100) + '[enc.1.push]\nkind = "layer-inc"\n')
        e.handle(ev("key.1", "down", 0.0))
        e.handle(ev("enc.1.push", "down", 0.02))
        self.assertEqual(e.layer, 2)
        self.assertEqual(values(run(e, 0.02, 0.2))[-1], 100)

    def test_release_goes_to_the_binding_the_press_started(self):
        e = engine(
            '[key.1.layers.1]\nkind = "cc-momentary"\ncc = 20\nhigh = 100\nfall-ms = 100\n'
            '[key.1.layers.2]\nkind = "cc-momentary"\ncc = 30\nhigh = 100\nfall-ms = 100\n'
            '[enc.1.push]\nkind = "layer-inc"\n'
        )
        e.handle(ev("key.1", "down", 0.0))
        e.handle(ev("enc.1.push", "down", 0.1))
        self.assertEqual(e.handle(ev("key.1", "up", 0.2)), [])
        self.assertEqual(run(e, 0.2, 0.4)[-1], (0.3, cc(1, 20, 0)))

    def test_release_all_jumps_held_momentary_to_low_and_other_glides_to_target(self):
        e = engine(
            momentary(rise=100, low=3)
            + '[key.2]\nkind = "cc-step"\ncc = 21\nstep = 40\nease-ms = 100\n'
        )
        e.handle(ev("key.1", "down", 0.0))
        e.handle(ev("key.2", "down", 0.0))
        run(e, 0.0, 0.03)
        self.assertEqual(e.release_all(), [cc(1, 20, 3), cc(1, 21, 40)])
        self.assertIsNone(e.next_due())
        self.assertEqual(run(e, 0.03, 0.3), [])
        self.assertEqual(e.release_all(), [])

    def test_release_all_lets_a_falling_glide_jump_to_its_target(self):
        e = engine(momentary(rise=0, fall=100))
        e.handle(ev("key.1", "down", 0.0))
        e.handle(ev("key.1", "up", 0.0))
        run(e, 0.0, 0.03)
        self.assertEqual(e.release_all(), [cc(1, 20, 0)])

    def test_release_all_keeps_a_latched_value_and_the_value_table(self):
        e = engine(momentary(rise=100, extra='mode = "latch"\n'))
        e.handle(ev("key.1", "down", 0.0))
        run(e, 0.0, 0.2)
        self.assertEqual(e.release_all(), [])
        self.assertEqual(e.cc_value(1, 20), 100)


if __name__ == "__main__":
    unittest.main()
