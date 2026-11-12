# SPDX-License-Identifier: GPL-3.0-only

import tempfile
import unittest
from pathlib import Path

from glra_osc.mapping import (
    AbsoluteTurn,
    CcBinding,
    MappingError,
    NoteBinding,
    RelativeTurn,
    default_mapping_path,
    load_mapping,
    parse_mapping,
)


class DefaultMappingTests(unittest.TestCase):
    def setUp(self):
        self.m = load_mapping()

    def test_file_ships_with_the_package(self):
        self.assertTrue(default_mapping_path().is_file())

    def test_globals(self):
        self.assertEqual(self.m.port, "GLRA K16")
        self.assertEqual(self.m.channel, 1)
        self.assertEqual(self.m.midi_channel, 0)

    def test_keys_are_notes_36_to_51(self):
        self.assertEqual(sorted(self.m.keys), list(range(1, 17)))
        for n, binding in self.m.keys.items():
            self.assertEqual(binding, NoteBinding(note=35 + n, velocity=127, mode="momentary"))

    def test_encoders_send_relative_twos_complement_ccs(self):
        self.assertEqual(sorted(self.m.enc_turn), [1, 2, 3])
        for n, turn in self.m.enc_turn.items():
            self.assertEqual(turn, RelativeTurn(cc=15 + n, encoding="twos-complement"))

    def test_encoder_pushes_are_notes_after_the_keys(self):
        self.assertEqual([self.m.enc_push[n].note for n in (1, 2, 3)], [52, 53, 54])


class ParseTests(unittest.TestCase):
    def test_empty_file_gives_defaults_and_no_controls(self):
        m = parse_mapping("")
        self.assertEqual((m.port, m.channel), ("GLRA K16", 1))
        self.assertEqual((m.keys, m.enc_push, m.enc_turn), ({}, {}, {}))

    def test_cc_binding_with_overrides(self):
        m = parse_mapping("[key.3]\ncc = 20\non = 100\noff = 10\nmode = 'toggle'\n")
        self.assertEqual(m.keys[3], CcBinding(cc=20, on=100, off=10, mode="toggle"))

    def test_cc_binding_defaults(self):
        m = parse_mapping("[key.3]\ncc = 20\n")
        self.assertEqual(m.keys[3], CcBinding(cc=20, on=127, off=0, mode="momentary"))

    def test_note_binding_on_encoder_push(self):
        m = parse_mapping("[enc.2.push]\nnote = 60\nvelocity = 90\nmode = 'toggle'\n")
        self.assertEqual(m.enc_push[2], NoteBinding(note=60, velocity=90, mode="toggle"))

    def test_absolute_turn(self):
        m = parse_mapping("[enc.1.turn]\ntype = 'absolute'\ncc = 7\ninitial = 100\nstep = 4\n")
        self.assertEqual(m.enc_turn[1], AbsoluteTurn(cc=7, initial=100, step=4))

    def test_absolute_turn_defaults(self):
        m = parse_mapping("[enc.1.turn]\ntype = 'absolute'\ncc = 7\n")
        self.assertEqual(m.enc_turn[1], AbsoluteTurn(cc=7, initial=64, step=1))

    def test_relative_encodings(self):
        for enc in ("twos-complement", "binary-offset", "signed-bit"):
            m = parse_mapping(f"[enc.3.turn]\ntype = 'relative'\ncc = 9\nencoding = '{enc}'\n")
            self.assertEqual(m.enc_turn[3], RelativeTurn(cc=9, encoding=enc))

    def test_relative_defaults_to_twos_complement(self):
        m = parse_mapping("[enc.3.turn]\ntype = 'relative'\ncc = 9\n")
        self.assertEqual(m.enc_turn[3].encoding, "twos-complement")

    def test_channel_and_port(self):
        m = parse_mapping("[global]\nport = 'Pad'\nchannel = 16\n")
        self.assertEqual((m.port, m.channel, m.midi_channel), ("Pad", 16, 15))

    def test_partial_mapping_leaves_other_controls_unmapped(self):
        m = parse_mapping("[key.16]\nnote = 1\n")
        self.assertEqual(list(m.keys), [16])


class ErrorTests(unittest.TestCase):
    def assertError(self, text, *fragments):
        with self.assertRaises(MappingError) as ctx:
            parse_mapping(text, source="test.toml")
        message = str(ctx.exception)
        self.assertTrue(message.startswith("test.toml: "), message)
        for fragment in fragments:
            self.assertIn(fragment, message)

    def test_bad_toml(self):
        self.assertError("[key.1\n", "not valid TOML")

    def test_unknown_top_level_key(self):
        self.assertError("[keys.1]\nnote = 1\n", "keys: unknown key")

    def test_unknown_global_key(self):
        self.assertError("[global]\nchanel = 2\n", "global.chanel: unknown key")

    def test_key_number_out_of_range(self):
        self.assertError("[key.17]\nnote = 1\n", "key.17", "1..16")
        self.assertError("[key.0]\nnote = 1\n", "key.0", "1..16")
        self.assertError("[enc.4.push]\nnote = 1\n", "enc.4", "1..3")

    def test_key_number_not_a_number(self):
        self.assertError("[key.a]\nnote = 1\n", "key.a")

    def test_channel_range(self):
        self.assertError("[global]\nchannel = 0\n", "global.channel", "1..16")
        self.assertError("[global]\nchannel = 17\n", "global.channel", "1..16")

    def test_port_must_be_nonempty_string(self):
        self.assertError("[global]\nport = ''\n", "global.port")
        self.assertError("[global]\nport = 3\n", "global.port")

    def test_note_out_of_range(self):
        self.assertError("[key.1]\nnote = 128\n", "key.1.note", "0..127", "128")
        self.assertError("[key.1]\nnote = -1\n", "key.1.note")

    def test_wrong_types(self):
        self.assertError("[key.1]\nnote = 'C3'\n", "key.1.note", "'C3'")
        self.assertError("[key.1]\nnote = 60.0\n", "key.1.note")
        self.assertError("[key.1]\nnote = true\n", "key.1.note")

    def test_velocity_zero_rejected(self):
        self.assertError("[key.1]\nnote = 60\nvelocity = 0\n", "key.1.velocity", "1..127")

    def test_binding_needs_exactly_one_of_note_or_cc(self):
        self.assertError("[key.1]\nvelocity = 5\n", "key.1", "'note' or 'cc'")
        self.assertError("[key.1]\nnote = 1\ncc = 2\n", "key.1", "'note' or 'cc'")

    def test_note_binding_rejects_cc_fields(self):
        self.assertError("[key.1]\nnote = 1\non = 5\n", "key.1.on: unknown key")

    def test_bad_mode(self):
        self.assertError("[key.1]\nnote = 1\nmode = 'latch'\n", "key.1.mode", "'latch'")

    def test_cc_values_range(self):
        self.assertError("[key.1]\ncc = 1\non = 200\n", "key.1.on")
        self.assertError("[key.1]\ncc = 1\noff = -1\n", "key.1.off")

    def test_key_table_must_be_a_table(self):
        self.assertError("[key]\n1 = 5\n", "key.1", "expected a table")

    def test_turn_type_required_and_checked(self):
        self.assertError("[enc.1.turn]\ncc = 1\n", "enc.1.turn.type", "None")
        self.assertError("[enc.1.turn]\ntype = 'spin'\ncc = 1\n", "enc.1.turn.type", "'spin'")

    def test_turn_cc_required(self):
        self.assertError("[enc.2.turn]\ntype = 'relative'\n", "enc.2.turn.cc", "required")

    def test_bad_relative_encoding(self):
        self.assertError(
            "[enc.1.turn]\ntype = 'relative'\ncc = 1\nencoding = 'gray'\n",
            "enc.1.turn.encoding",
            "twos-complement",
            "'gray'",
        )

    def test_absolute_step_and_initial(self):
        self.assertError("[enc.1.turn]\ntype = 'absolute'\ncc = 1\nstep = 0\n", "enc.1.turn.step")
        self.assertError(
            "[enc.1.turn]\ntype = 'absolute'\ncc = 1\ninitial = 128\n", "enc.1.turn.initial"
        )

    def test_relative_rejects_absolute_fields(self):
        self.assertError(
            "[enc.1.turn]\ntype = 'relative'\ncc = 1\nstep = 2\n", "enc.1.turn.step: unknown key"
        )

    def test_unknown_encoder_field(self):
        self.assertError("[enc.1.spin]\ncc = 1\n", "enc.1.spin: unknown key")


class LoadTests(unittest.TestCase):
    def test_load_from_path(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "m.toml"
            path.write_text("[key.1]\nnote = 40\n")
            self.assertEqual(load_mapping(path).keys[1].note, 40)

    def test_missing_file(self):
        with self.assertRaises(MappingError) as ctx:
            load_mapping("/nonexistent/m.toml")
        self.assertIn("/nonexistent/m.toml", str(ctx.exception))

    def test_error_from_file_names_the_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.toml"
            path.write_text("[key.1]\nnote = 999\n")
            with self.assertRaises(MappingError) as ctx:
                load_mapping(path)
            self.assertIn("bad.toml", str(ctx.exception))
            self.assertIn("key.1.note", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
