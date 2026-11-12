# SPDX-License-Identifier: GPL-3.0-only

import collections
import json
import unittest
from pathlib import Path

from glra_osc.decode import Decoder, load_layout
from glra_osc.events import ControlEvent, format_event
from glra_osc.monitor import render

FIXTURE = Path(__file__).parent / "fixtures" / "captured_reports.jsonl"


def keys(*usages):
    return bytes([0, 0, *usages]) + bytes(6 - len(usages))


def pairs(events):
    return [(e.control, e.action) for e in events]


def captured(run):
    return [r for r in map(json.loads, FIXTURE.read_text().splitlines()) if r["run"] == run]


class KeyDecodeTests(unittest.TestCase):
    def setUp(self):
        self.d = Decoder()

    def test_press_and_release(self):
        self.assertEqual(pairs(self.d.feed("keys", keys(0x56), 1.0)), [("key.1", "down")])
        self.assertEqual(pairs(self.d.feed("keys", keys(), 1.1)), [("key.1", "up")])

    def test_two_keys_held_then_released_one_by_one(self):
        self.d.feed("keys", keys(0x56), 0)
        self.assertEqual(pairs(self.d.feed("keys", keys(0x56, 0x57), 1)), [("key.2", "down")])
        self.assertEqual(pairs(self.d.feed("keys", keys(0x56), 2)), [("key.2", "up")])
        self.assertEqual(pairs(self.d.feed("keys", keys(), 3)), [("key.1", "up")])

    def test_repeated_identical_report_gives_no_event(self):
        self.d.feed("keys", keys(0x56), 0)
        self.assertEqual(self.d.feed("keys", keys(0x56), 1), [])

    def test_rollover_error_is_ignored_and_keeps_state(self):
        self.d.feed("keys", keys(0x56), 0)
        self.assertEqual(self.d.feed("keys", keys(1, 1, 1, 1, 1, 1), 1), [])
        self.assertEqual(pairs(self.d.feed("keys", keys(), 2)), [("key.1", "up")])

    def test_unknown_usage_and_short_report(self):
        self.assertEqual(pairs(self.d.feed("keys", keys(0x04), 0)), [("key.unknown:0x04", "down")])
        self.assertEqual(self.d.feed("keys", b"\x00", 0), [])

    def test_timestamp_is_carried(self):
        (e,) = self.d.feed("keys", keys(0x56), 12.5)
        self.assertEqual(e, ControlEvent("key.1", "down", 12.5))

    def test_reset_forgets_held_keys(self):
        self.d.feed("keys", keys(0x56), 0)
        self.d.reset()
        self.assertEqual(pairs(self.d.feed("keys", keys(0x56), 1)), [("key.1", "down")])


class ConsumerDecodeTests(unittest.TestCase):
    def setUp(self):
        self.d = Decoder()

    def test_turn_counts_once_at_the_press(self):
        self.assertEqual(pairs(self.d.feed("consumer", b"\x03\xe9\x00", 0)), [("enc.?", "cw")])
        self.assertEqual(self.d.feed("consumer", b"\x03\x00\x00", 0.001), [])
        self.assertEqual(pairs(self.d.feed("consumer", b"\x03\xea\x00", 1)), [("enc.?", "ccw")])
        self.assertEqual(self.d.feed("consumer", b"\x03\x00\x00", 1.001), [])

    def test_push_down_then_real_release(self):
        self.assertEqual(
            pairs(self.d.feed("consumer", b"\x03\xe2\x00", 0)), [("enc.?.push", "down")]
        )
        self.assertEqual(
            pairs(self.d.feed("consumer", b"\x03\x00\x00", 0.3)), [("enc.?.push", "up")]
        )

    def test_turn_replacing_a_held_push_releases_it_first(self):
        self.d.feed("consumer", b"\x03\xe2\x00", 0)
        self.assertEqual(
            pairs(self.d.feed("consumer", b"\x03\xe9\x00", 1)),
            [("enc.?.push", "up"), ("enc.?", "cw")],
        )

    def test_unknown_usage_and_other_report_id(self):
        self.assertEqual(
            pairs(self.d.feed("consumer", b"\x03\xcd\x00", 0)),
            [("consumer.unknown:0x00cd", "down")],
        )
        self.assertEqual(self.d.feed("consumer", b"\x02\xe9\x00", 0), [])

    def test_unknown_source_raises(self):
        with self.assertRaises(ValueError):
            self.d.feed("vendor", b"\x00", 0)


class LayoutTests(unittest.TestCase):
    def test_packaged_layout_is_provisional_with_sixteen_keys(self):
        layout = load_layout()
        self.assertTrue(layout["provisional"])
        self.assertEqual(sorted(layout["keys"].values()), sorted(f"key.{n}" for n in range(1, 17)))


class CapturedFixtureTests(unittest.TestCase):
    """Replays the 2026-11-12 raw captures (tests/fixtures/captured_reports.jsonl)."""

    def decode_all(self, run):
        d, out = Decoder(), []
        for r in captured(run):
            out += [(r["step"], e) for e in d.feed(r["source"], bytes.fromhex(r["hex"]), r["t"])]
        return out

    def test_each_key_step_presses_its_own_key(self):
        # Releases can land in the next step (Bob's prompts ran fast), so check downs only.
        events = self.decode_all("capture")
        for n in range(1, 17):
            if n == 7:  # no report in either pass; see notes
                continue
            downs = {e.control for step, e in events if step == f"key{n}" and e.action == "down"}
            self.assertEqual(downs, {f"key.{n}"}, f"key{n}")
        self.assertFalse([e for step, e in events if step == "key7"])

    def test_key_downs_and_ups_pair_up_across_the_capture(self):
        # The capture ends with key 1 still held (the combo-key-dial step's release is missing).
        events = [e for _, e in self.decode_all("capture") if e.control.startswith("key.")]
        downs = collections.Counter(e.control for e in events if e.action == "down")
        ups = collections.Counter(e.control for e in events if e.action == "up")
        ups["key.1"] += 1
        self.assertEqual(downs, ups)

    def test_dial_events_match_raw_report_counts(self):
        raw = collections.Counter(
            r["hex"] for r in captured("capture") if r["source"] == "consumer"
        )
        events = [e for _, e in self.decode_all("capture") if e.control.startswith("enc.")]
        got = collections.Counter((e.control, e.action) for e in events)
        self.assertEqual(got[("enc.?", "cw")], raw["03e900"])
        self.assertEqual(got[("enc.?", "ccw")], raw["03ea00"])
        self.assertEqual(got[("enc.?.push", "down")], raw["03e200"])
        self.assertEqual(got[("enc.?.push", "up")], raw["03e200"])

    def test_replug_capture_decodes(self):
        events = [e for _, e in self.decode_all("replug")]
        self.assertIn(("key.1", "down"), pairs(events))
        self.assertIn(("enc.?", "ccw"), pairs(events))


class FormatTests(unittest.TestCase):
    def test_lines(self):
        wall = 1_700_000_000.122
        self.assertRegex(
            format_event(ControlEvent("key.7", "down", 0), wall),
            r"^\[\d\d:\d\d:\d\d\.122\] KEY 07 DOWN$",
        )
        self.assertTrue(format_event(ControlEvent("enc.?", "cw", 0), wall).endswith("ENC ? CW"))
        self.assertTrue(
            format_event(ControlEvent("enc.2.push", "up", 0), wall).endswith("ENC 2 PUSH UP")
        )

    def test_render_adds_raw_line_only_when_asked(self):
        d = Decoder()
        plain = render(d, "keys", keys(0x56), 0, 1_700_000_000.0)
        self.assertEqual(len(plain), 1)
        d = Decoder()
        raw = render(d, "keys", keys(0x56), 0, 1_700_000_000.0, raw=True)
        self.assertEqual(len(raw), 2)
        self.assertTrue(raw[0].endswith("RAW keys 0000560000000000"))


if __name__ == "__main__":
    unittest.main()
