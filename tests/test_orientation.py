# SPDX-License-Identifier: GPL-3.0-only

import unittest

from glra_midi import orientation as o
from glra_midi.decode import load_layout
from glra_midi.events import ControlEvent, format_event
from glra_midi.monitor import render
from glra_midi.decode import Decoder

ALL = o.ORIENTATIONS

# The worked 4x4 table for dials-right from docs/config-app.md §6.2: the physical key
# in each displayed cell, row by row. Displayed key 1 = key.13, displayed key 4 = key.1.
DIALS_RIGHT = [
    [13, 9, 5, 1],
    [14, 10, 6, 2],
    [15, 11, 7, 3],
    [16, 12, 8, 4],
]
# The other three, derived by hand from the same formulas (§6.2 table):
DIALS_BOTTOM = [
    [16, 15, 14, 13],
    [12, 11, 10, 9],
    [8, 7, 6, 5],
    [4, 3, 2, 1],
]
DIALS_LEFT = [
    [4, 8, 12, 16],
    [3, 7, 11, 15],
    [2, 6, 10, 14],
    [1, 5, 9, 13],
]
DIALS_TOP = [
    [1, 2, 3, 4],
    [5, 6, 7, 8],
    [9, 10, 11, 12],
    [13, 14, 15, 16],
]
TABLES = {
    "dials-top": DIALS_TOP,
    "dials-right": DIALS_RIGHT,
    "dials-bottom": DIALS_BOTTOM,
    "dials-left": DIALS_LEFT,
}


class KeyTests(unittest.TestCase):
    def test_worked_tables(self):
        for name, table in TABLES.items():
            with self.subTest(name):
                for row in range(4):
                    for col in range(4):
                        physical = table[row][col]
                        self.assertEqual(o.key_cell(name, physical), (row, col))
                        self.assertEqual(o.key_number(name, physical), row * 4 + col + 1)
                        self.assertEqual(o.physical_key(name, row * 4 + col + 1), physical)

    def test_dials_right_by_eye(self):
        self.assertEqual(o.physical_key("dials-right", 1), 13)
        self.assertEqual(o.physical_key("dials-right", 4), 1)
        self.assertEqual(o.key_number("dials-right", 1), 4)
        self.assertEqual(o.key_number("dials-right", 13), 1)

    def test_each_rotation_is_a_bijection(self):
        for name in ALL:
            with self.subTest(name):
                shown = [o.key_number(name, k) for k in range(1, 17)]
                self.assertEqual(sorted(shown), list(range(1, 17)))
                for k in range(1, 17):
                    self.assertEqual(o.physical_key(name, o.key_number(name, k)), k)
                    self.assertEqual(o.key_number(name, o.physical_key(name, k)), k)
                cells = {o.key_cell(name, k) for k in range(1, 17)}
                self.assertEqual(len(cells), 16)

    def test_four_quarter_turns_return_to_the_start(self):
        for row in range(4):
            for col in range(4):
                cell = (row, col)
                for _ in range(4):
                    cell = o.quarter_turn(*cell)
                self.assertEqual(cell, (row, col))

    def test_orientations_are_successive_quarter_turns(self):
        for k in range(1, 17):
            cell = ((k - 1) // 4, (k - 1) % 4)
            for name in ALL:
                self.assertEqual(o.key_cell(name, k), cell, name)
                cell = o.quarter_turn(*cell)

    def test_unturn_inverts_turn(self):
        for name in ALL:
            for row in range(4):
                for col in range(4):
                    shown = o.turn_cell(name, row, col)
                    self.assertEqual(o.unturn_cell(name, *shown), (row, col))

    def test_dials_top_matches_layout_json(self):
        layout = load_layout()
        for control in layout["keys"].values():
            kind, n, part = o.display_control("dials-top", control)
            self.assertEqual((kind, part), ("key", ""))
            self.assertEqual(f"key.{n}", control)  # displayed number = physical number
        for entry in layout["consumer"].values():
            control = entry["control"]
            kind, n, part = o.display_control("dials-top", control)
            self.assertEqual(kind, "enc")
            self.assertEqual(control.split(".")[1], str(n))
        # layout.json grid: key 1 top-left, row-major
        self.assertEqual(o.key_cell("dials-top", 1), (0, 0))
        self.assertEqual(o.key_cell("dials-top", 16), (3, 3))

    def test_out_of_range(self):
        with self.assertRaises(ValueError):
            o.key_number("dials-top", 0)
        with self.assertRaises(ValueError):
            o.physical_key("dials-top", 17)
        with self.assertRaises(ValueError):
            o.key_number("sideways", 1)
        with self.assertRaises(ValueError):
            o.key_number("dials-top", True)


class DialTests(unittest.TestCase):
    def test_displayed_dial_order(self):
        expected = {
            "dials-top": (1, 2, 3),
            "dials-right": (1, 2, 3),
            "dials-bottom": (3, 2, 1),
            "dials-left": (3, 2, 1),
        }
        for name, order in expected.items():
            for shown, physical in enumerate(order, 1):
                self.assertEqual(o.physical_dial(name, shown), physical, name)
                self.assertEqual(o.dial_number(name, physical), shown, name)

    def test_bijection(self):
        for name in ALL:
            self.assertEqual(sorted(o.dial_number(name, d) for d in (1, 2, 3)), [1, 2, 3])
            for d in (1, 2, 3):
                self.assertEqual(o.physical_dial(name, o.dial_number(name, d)), d)

    def test_sides(self):
        self.assertEqual(
            [o.dial_side(n) for n in ALL], ["top", "right", "bottom", "left"]
        )

    def test_dial_order_follows_the_physical_rotation(self):
        # Dial i sits at the left/top end of the row of dials when enc.1 is at the start of the
        # edge; rotating clockwise a quarter turn sends the top edge to the right edge with
        # enc.1 at the top, and so on. Check against the same rotation applied to a
        # coordinate along the top edge: enc n at column n-1 (and row -1, above the grid).
        # Rotate using extended coordinates with the dials one step outside the grid.
        # dials-top: (row -1, col c); a quarter turn maps (r, c) -> (c, 3 - r).
        for name_index, name in enumerate(ALL):
            along = {}
            for enc in (1, 2, 3):
                r, c = -1, enc - 1  # dials-top: above the grid; enc.1 leftmost (col 0)
                for _ in range(name_index):
                    r, c = c, 3 - r
                along[enc] = (r, c)
            side = o.dial_side(name)
            if side in ("top", "bottom"):
                ranked = sorted(along, key=lambda e: along[e][1])  # left to right
            else:
                ranked = sorted(along, key=lambda e: along[e][0])  # top to bottom
            self.assertEqual(
                ranked, [o.physical_dial(name, n) for n in (1, 2, 3)], name
            )


class ControlNameTests(unittest.TestCase):
    def test_display_control(self):
        self.assertEqual(o.display_control("dials-right", "key.13"), ("key", 1, ""))
        self.assertEqual(o.display_control("dials-bottom", "enc.3.push"), ("enc", 1, "push"))
        self.assertEqual(o.display_control("dials-left", "enc.1.turn"), ("enc", 3, "turn"))
        self.assertEqual(o.display_control("dials-top", "enc.2"), ("enc", 2, ""))
        self.assertEqual(o.display_control("dials-top", "enc.?"), ("enc", None, ""))

    def test_label(self):
        self.assertEqual(o.label("dials-right", "key.1"), "Key 4")
        self.assertEqual(o.label("dials-bottom", "enc.3.push"), "Dial 1 push")
        self.assertEqual(o.label("dials-top", "enc.2.turn"), "Dial 2 turn")

    def test_not_a_control(self):
        for bad in ("key.unknown:0x65", "key", "key.1.push", "enc.1.spin", "mouse.1", "key.x"):
            with self.assertRaises(ValueError, msg=bad):
                o.display_control("dials-top", bad)

    def test_turns_stay_physical(self):
        # cw/ccw aren't touched: display_control only renumbers, never reads the action.
        for name in ALL:
            self.assertEqual(o.display_control(name, "enc.2")[0], "enc")


class EventLabelTests(unittest.TestCase):
    WALL = 1_700_000_000.0

    def test_default_is_unchanged(self):
        self.assertTrue(
            format_event(ControlEvent("key.7", "down", 0), self.WALL).endswith("KEY 07 DOWN")
        )

    def test_dials_right_key(self):
        line = format_event(ControlEvent("key.13", "down", 0), self.WALL, "dials-right")
        self.assertTrue(line.endswith("KEY 01 [key.13] DOWN"), line)

    def test_dials_top_still_shows_brackets(self):
        line = format_event(ControlEvent("key.7", "up", 0), self.WALL, "dials-top")
        self.assertTrue(line.endswith("KEY 07 [key.7] UP"), line)

    def test_dials(self):
        line = format_event(ControlEvent("enc.1.push", "down", 0), self.WALL, "dials-bottom")
        self.assertTrue(line.endswith("ENC 3 PUSH [enc.1.push] DOWN"), line)
        line = format_event(ControlEvent("enc.1", "cw", 0), self.WALL, "dials-left")
        self.assertTrue(line.endswith("ENC 3 [enc.1] CW"), line)  # cw stays cw

    def test_unknown_names_keep_the_plain_label(self):
        line = format_event(ControlEvent("key.unknown:0x65", "down", 0), self.WALL, "dials-right")
        self.assertTrue(line.endswith("KEY.UNKNOWN:0X65 DOWN"), line)
        line = format_event(ControlEvent("enc.?", "cw", 0), self.WALL, "dials-right")
        self.assertTrue(line.endswith("ENC ? [enc.?] CW"), line)

    def test_render_passes_orientation(self):
        d = Decoder()
        report = bytes([0, 0, 0x4D, 0, 0, 0, 0, 0])  # 0x4d = key.13 in layout.json
        (line,) = render(d, "keys", report, 0, self.WALL, orientation="dials-right")
        self.assertTrue(line.endswith("KEY 01 [key.13] DOWN"), line)


if __name__ == "__main__":
    unittest.main()
