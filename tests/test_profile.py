# SPDX-License-Identifier: GPL-3.0-only

import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from glra_midi import profile
from glra_midi.profile import (
    CONTROL_NAMES,
    CcAbsolute,
    CcMomentary,
    CcRelative,
    CcSet,
    CcStep,
    LayerDec,
    LayerInc,
    LayerSet,
    NO_LAYER,
    Lighting,
    Note,
    PerLayer,
    Profile,
    ProfileError,
    add_layer,
    app_dir,
    check_profile_name,
    clear_event,
    control_shape,
    current_profile_path,
    default_profile_path,
    dump_profile,
    dumps_profile,
    load_profile,
    make_global,
    make_per_layer,
    parse_profile,
    profile_path,
    migrate_app_dir,
    profiles_dir,
    remove_layer,
    rename_layer,
    set_current,
    set_event,
    set_layer_key,
    validate,
)

# docs/config-app.md section 2.5, as written there.
DESIGN_EXAMPLE = """\
version = 1

[midi]
port = "GLRA K16"
channel = 1

[pad]
orientation = "dials-top"

[layers]
count = 4
names = ["Drums", "Synth", "", "Mixer"]

[lighting]
mode = 2            # Breathing
brightness = 4      # 0..4
speed = 2           # 0..4
color = [0, 255, 255]   # fixed hue h, s, v (0..255); leave out for the mode's own colours

[key.1]
kind = "note"
note = 36
velocity = 110

[key.2.layers.1]
kind = "note"
note = 37
mode = "latch"

[key.2.layers.2]
kind = "cc-momentary"
cc = 20
low = 10
high = 120
rise-ms = 250
fall-ms = 600
curve = "ease-out"
channel = 2

[key.3]
kind = "cc-set"
cc = 21
value = 64

[key.4.layers.1]
kind = "cc-step"
cc = 21
step = 8
ease-ms = 120
curve = "ease-in-out"

[key.8.layers.1]
kind = "cc-step"
cc = 21
step = -8
ease-ms = 120
curve = "ease-in-out"

[key.13]
kind = "layer-set"
layer = 1

[enc.1.push]
kind = "layer-dec"

[enc.3.push]
kind = "layer-inc"

[enc.1.turn]
kind = "cc-relative"
cc = 16

[enc.2.turn.layers.1]
kind = "cc-absolute"
cc = 21
step = 2
initial = 64

[enc.2.turn.layers.2]
kind = "cc-relative"
cc = 17
encoding = "binary-offset"
"""

# One profile using every kind, a channel, names, lighting and a per-layer turn.
EVERY_KIND = Profile(
    port="Test Port",
    channel=3,
    orientation="dials-left",
    layer_count=3,
    layer_names=("Drums", "", "Mixer"),
    lighting=Lighting(mode=4, brightness=2, speed=3, color=(10, 200, 255)),
    controls={
        "key.1": Note(note=36, velocity=100, mode="latch", channel=10),
        "key.2": PerLayer.of(
            {
                1: CcMomentary(cc=20, low=5, high=100, rise_ms=250, fall_ms=600, curve="ease-in", mode="latch"),
                3: CcSet(cc=21, value=64, channel=2),
            }
        ),
        "key.3": CcStep(cc=22, step=-8, ease_ms=120, curve="ease-in-out"),
        "key.4": LayerSet(layer=2),
        "key.5": LayerInc(),
        "key.6": LayerDec(),
        "key.7": Note(note=0),
        "enc.1.push": PerLayer.of({2: Note(note=60, channel=1)}),
        "enc.1.turn": CcRelative(cc=16, encoding="signed-bit", channel=4),
        "enc.2.turn": PerLayer.of(
            {1: CcAbsolute(cc=30, step=2, initial=64), 3: CcAbsolute(cc=31)}
        ),
        "enc.3.turn": CcAbsolute(cc=32, step=127, initial=0, channel=16),
    },
)


class ParseTests(unittest.TestCase):
    def test_every_kind_parses(self):
        text = """\
version = 1
[key.1]
kind = "note"
note = 40
[key.2]
kind = "cc-momentary"
cc = 1
[key.3]
kind = "cc-set"
cc = 2
value = 3
[key.4]
kind = "cc-step"
cc = 4
step = 5
[key.5]
kind = "layer-set"
layer = 4
[key.6]
kind = "layer-inc"
[key.7]
kind = "layer-dec"
[enc.1.turn]
kind = "cc-relative"
cc = 6
[enc.2.turn]
kind = "cc-absolute"
cc = 7
"""
        p = parse_profile(text)
        self.assertEqual(
            p.controls,
            {
                "key.1": Note(note=40),
                "key.2": CcMomentary(cc=1),
                "key.3": CcSet(cc=2, value=3),
                "key.4": CcStep(cc=4, step=5),
                "key.5": LayerSet(layer=4),
                "key.6": LayerInc(),
                "key.7": LayerDec(),
                "enc.1.turn": CcRelative(cc=6),
                "enc.2.turn": CcAbsolute(cc=7),
            },
        )

    def test_defaults(self):
        p = parse_profile("version = 1\n")
        self.assertEqual(
            (p.port, p.channel, p.orientation, p.layer_count, p.layer_names, p.lighting),
            ("GLRA K16", 1, "dials-top", 4, ("", "", "", ""), None),
        )
        self.assertEqual(p.controls, {})
        self.assertEqual(p.midi_channel, 0)

    def test_event_defaults(self):
        p = parse_profile('version = 1\n[key.1]\nkind = "cc-momentary"\ncc = 9\n')
        self.assertEqual(
            p.controls["key.1"],
            CcMomentary(
                cc=9, low=0, high=127, rise_ms=0, fall_ms=0, curve="linear", mode="momentary", channel=None
            ),
        )

    def test_design_example(self):
        p = parse_profile(DESIGN_EXAMPLE)
        self.assertEqual(p.layer_names, ("Drums", "Synth", "", "Mixer"))
        self.assertEqual(p.lighting, Lighting(mode=2, brightness=4, speed=2, color=(0, 255, 255)))
        self.assertEqual(p.controls["key.1"], Note(note=36, velocity=110))
        self.assertEqual(p.action("key.2", 1), Note(note=37, mode="latch"))
        self.assertEqual(
            p.action("key.2", 2),
            CcMomentary(cc=20, low=10, high=120, rise_ms=250, fall_ms=600, curve="ease-out", channel=2),
        )
        self.assertIsNone(p.action("key.2", 3))
        self.assertEqual(p.action("key.8", 1), CcStep(cc=21, step=-8, ease_ms=120, curve="ease-in-out"))
        self.assertEqual(p.action("key.13", 4), LayerSet(layer=1))  # global: every layer
        self.assertEqual(p.action("enc.2.turn", 1), CcAbsolute(cc=21, step=2, initial=64))
        self.assertEqual(p.action("enc.2.turn", 2), CcRelative(cc=17, encoding="binary-offset"))
        self.assertEqual(validate(p), [])

    def test_controls_come_out_in_canonical_order(self):
        text = (
            'version = 1\n[enc.1.turn]\nkind = "cc-relative"\ncc = 1\n'
            '[key.10]\nkind = "layer-inc"\n[key.2]\nkind = "layer-inc"\n'
            '[enc.1.push]\nkind = "layer-inc"\n'
        )
        self.assertEqual(
            list(parse_profile(text).controls), ["key.2", "key.10", "enc.1.push", "enc.1.turn"]
        )

    def test_names_pad_to_count(self):
        p = parse_profile('version = 1\n[layers]\ncount = 3\nnames = ["A"]\n')
        self.assertEqual(p.layer_names, ("A", "", ""))

    def test_shape_and_action(self):
        p = parse_profile(DESIGN_EXAMPLE)
        self.assertEqual(control_shape(p.controls["key.1"]), "global")
        self.assertEqual(control_shape(p.controls["key.2"]), "per-layer")
        self.assertEqual(control_shape(p.controls["key.13"]), "layer-key")
        self.assertEqual(control_shape(p.controls.get("key.16")), "none")


class ErrorTests(unittest.TestCase):
    def assertError(self, text, *fragments, start=None):
        with self.assertRaises(ProfileError) as ctx:
            parse_profile(text, source="test.toml")
        message = str(ctx.exception)
        self.assertTrue(message.startswith("test.toml: "), message)
        if start is not None:
            self.assertTrue(message.removeprefix("test.toml: ").startswith(start), message)
        for fragment in fragments:
            self.assertIn(fragment, message)

    def key(self, body, name="key.1"):
        return f"version = 1\n[{name}]\n{body}"

    def test_cc_momentary_has_no_ease_ms(self):
        self.assertError(
            self.key("kind = 'cc-momentary'\ncc = 1\nease-ms = 5\n"), start="key.1.ease-ms"
        )
        self.assertError(
            self.key("kind = 'cc-momentary'\ncc = 1\nfall-ms = 10001\n"), start="key.1.fall-ms"
        )

    def test_bad_toml(self):
        self.assertError("version = 1\n[key.1\n", "not valid TOML")

    def test_version(self):
        self.assertError("version = 2\n", "version", "got 2", start="version")
        self.assertError("version = true\n", start="version")
        self.assertError('version = "1"\n', start="version")
        self.assertError("version = 1.0\n", "got 1.0", start="version")

    def test_a_number_in_a_table_name_has_one_spelling(self):
        # Review 11: `[key."01"]` used to load as key 1, and beat a `[key.1]` written before it.
        note = "kind = 'note'\nnote = 36\n"
        for name in ('key."01"', 'key."+1"', 'key."001"', 'enc."01".push'):
            self.assertError(self.key(note, name), "unknown control", start=name.split(".")[0])
        self.assertError(
            "version = 1\n[key.1]\n" + note + '[key."01"]\nkind = \'note\'\nnote = 40\n',
            "unknown control",
        )
        self.assertError(
            "version = 1\n[key.1.layers.\"01\"]\n" + note, "layer doesn't exist", start="key.1.layers.01"
        )

    def test_unknown_top_level_key_including_legacy_global(self):
        self.assertError("version = 1\n[global]\nchannel = 2\n", start="global: unknown key")
        self.assertError("version = 1\n[keys.1]\n", start="keys: unknown key")

    def test_midi_section(self):
        self.assertError("version = 1\n[midi]\nchannel = 0\n", "1..16", start="midi.channel")
        self.assertError("version = 1\n[midi]\nchannel = 17\n", start="midi.channel")
        self.assertError("version = 1\n[midi]\nport = ''\n", start="midi.port")
        self.assertError("version = 1\n[midi]\nchanel = 1\n", start="midi.chanel: unknown key")

    def test_orientation(self):
        self.assertError("version = 1\n[pad]\norientation = 'up'\n", "dials-top", start="pad.orientation")

    def test_layers_section(self):
        self.assertError("version = 1\n[layers]\ncount = 0\n", start="layers.count")
        self.assertError("version = 1\n[layers]\ncount = 9\n", "1..8", start="layers.count")
        self.assertError(
            "version = 1\n[layers]\ncount = 2\nnames = ['a', 'b', 'c']\n", start="layers.names"
        )
        self.assertError("version = 1\n[layers]\nnames = [1]\n", start="layers.names")

    def test_lighting_section(self):
        self.assertError("version = 1\n[lighting]\nbrightness = 1\n", start="lighting.mode: required")
        self.assertError("version = 1\n[lighting]\nmode = 13\n", start="lighting.mode")
        self.assertError("version = 1\n[lighting]\nmode = 1\nbrightness = 5\n", start="lighting.brightness")
        self.assertError("version = 1\n[lighting]\nmode = 1\nspeed = -1\n", start="lighting.speed")
        self.assertError("version = 1\n[lighting]\nmode = 1\ncolor = [1, 2]\n", start="lighting.color")
        self.assertError("version = 1\n[lighting]\nmode = 1\ncolor = [1, 2, 256]\n", start="lighting.color")
        self.assertError(
            "version = 1\n[lighting]\nmode = 3\ncolor = [1, 2, 3]\n",
            "mode 3 doesn't take a single colour",
            start="lighting.color",
        )
        self.assertError("version = 1\n[lighting]\nmode = 1\nhue = 1\n", start="lighting.hue: unknown key")

    def test_control_number_out_of_range(self):
        self.assertError("version = 1\n[key.17]\nkind = 'layer-inc'\n", "1..16", start="key.17")
        self.assertError("version = 1\n[enc.4.push]\nkind = 'layer-inc'\n", "1..3", start="enc.4")
        self.assertError("version = 1\n[enc.1.spin]\nkind = 'layer-inc'\n", start="enc.1.spin: unknown key")

    def test_kind_required_and_checked(self):
        self.assertError(self.key("note = 1\n"), "kind", "layers", start="key.1")
        self.assertError("version = 1\n[key.1]\n", start="key.1")
        self.assertError(self.key("kind = 'spin'\n"), "'spin'", start="key.1.kind")
        self.assertError(
            "version = 1\n[key.1.layers.1]\ncc = 1\n", start="key.1.layers.1.kind: required"
        )

    def test_field_errors_name_their_path(self):
        self.assertError(self.key("kind = 'note'\nnote = 300\n"), "0..127", "300", start="key.1.note")
        self.assertError(self.key("kind = 'note'\n"), start="key.1.note: required")
        self.assertError(self.key("kind = 'note'\nnote = 'C3'\n"), start="key.1.note")
        self.assertError(self.key("kind = 'note'\nnote = 1.5\n"), start="key.1.note")
        self.assertError(self.key("kind = 'note'\nnote = true\n"), start="key.1.note")
        self.assertError(self.key("kind = 'note'\nnote = 1\nvelocity = 0\n"), start="key.1.velocity")
        self.assertError(self.key("kind = 'note'\nnote = 1\nmode = 'toggle'\n"), "latch", start="key.1.mode")
        self.assertError(self.key("kind = 'note'\nnote = 1\nchannel = 0\n"), start="key.1.channel")
        self.assertError(
            "version = 1\n[key.4.layers.2]\nkind = 'cc-set'\ncc = 300\nvalue = 1\n",
            start="key.4.layers.2.cc",
        )

    def test_unknown_key_for_kind(self):
        self.assertError(self.key("kind = 'note'\nnote = 1\ncc = 2\n"), start="key.1.cc: unknown key")
        self.assertError(self.key("kind = 'layer-inc'\nnote = 2\n"), start="key.1.note: unknown key")

    def test_ranges_per_kind(self):
        self.assertError(self.key("kind = 'cc-set'\ncc = 1\nvalue = 128\n"), start="key.1.value")
        self.assertError(self.key("kind = 'cc-step'\ncc = 1\nstep = 0\n"), "non-zero", start="key.1.step")
        self.assertError(self.key("kind = 'cc-step'\ncc = 1\nstep = 128\n"), start="key.1.step")
        self.assertError(self.key("kind = 'cc-step'\ncc = 1\nstep = 1\nease-ms = 10001\n"), start="key.1.ease-ms")
        self.assertError(self.key("kind = 'cc-step'\ncc = 1\nstep = 1\ncurve = 'wavy'\n"), "ease-in", start="key.1.curve")
        self.assertError(self.key("kind = 'cc-momentary'\ncc = 1\nhigh = 128\n"), start="key.1.high")
        self.assertError(self.key("kind = 'layer-set'\nlayer = 0\n"), start="key.1.layer")
        self.assertError(self.key("kind = 'layer-set'\nlayer = 9\n"), "1..8", start="key.1.layer")
        self.assertError(
            "version = 1\n[enc.1.turn]\nkind = 'cc-absolute'\ncc = 1\nstep = 0\n", start="enc.1.turn.step"
        )
        self.assertError(
            "version = 1\n[enc.1.turn]\nkind = 'cc-relative'\ncc = 1\nencoding = 'gray'\n",
            "twos-complement",
            start="enc.1.turn.encoding",
        )

    def test_layer_key_above_layer_count(self):
        self.assertError(
            "version = 1\n[layers]\ncount = 4\n[enc.2.push]\nkind = 'layer-set'\nlayer = 6\n",
            "layer 6 doesn't exist (count = 4)",
            start="enc.2.push.layer",
        )

    def test_layer_key_and_events_exclude_each_other(self):
        self.assertError(
            "version = 1\n[key.13]\nkind = 'layer-inc'\n[key.13.layers.1]\nkind = 'note'\nnote = 1\n",
            "a layer key can't also have per-layer events",
            start="key.13",
        )

    def test_global_and_per_layer_exclude_each_other(self):
        self.assertError(
            "version = 1\n[key.2]\nkind = 'note'\nnote = 1\n[key.2.layers.1]\nkind = 'note'\nnote = 2\n",
            "exclude each other",
            start="key.2",
        )

    def test_layer_key_in_a_layer_table(self):
        self.assertError(
            "version = 1\n[key.4.layers.1]\nkind = 'layer-inc'\n",
            "layer keys are global; move it to [key.4]",
            start="key.4.layers.1",
        )

    def test_dial_turn_can_not_be_a_layer_key_or_press_kind(self):
        self.assertError(
            "version = 1\n[enc.1.turn]\nkind = 'layer-inc'\n", "cc-relative", start="enc.1.turn.kind"
        )
        self.assertError(
            "version = 1\n[enc.1.turn.layers.1]\nkind = 'layer-inc'\n", start="enc.1.turn.layers.1.kind"
        )
        self.assertError("version = 1\n[enc.1.turn]\nkind = 'note'\nnote = 1\n", start="enc.1.turn.kind")

    def test_press_can_not_be_a_turn_kind(self):
        self.assertError(self.key("kind = 'cc-relative'\ncc = 1\n"), start="key.1.kind")
        self.assertError(
            "version = 1\n[enc.1.push]\nkind = 'cc-absolute'\ncc = 1\n", start="enc.1.push.kind"
        )

    def test_layer_table_out_of_range(self):
        self.assertError(
            "version = 1\n[layers]\ncount = 2\n[key.1.layers.3]\nkind = 'note'\nnote = 1\n",
            "count = 2",
            start="key.1.layers.3",
        )
        self.assertError(
            "version = 1\n[key.1.layers.0]\nkind = 'note'\nnote = 1\n", start="key.1.layers.0"
        )
        self.assertError(
            "version = 1\n[key.1.layers.x]\nkind = 'note'\nnote = 1\n", start="key.1.layers.x"
        )

    def test_empty_layers_table(self):
        self.assertError("version = 1\n[key.1]\nlayers = {}\n", start="key.1.layers")

    def test_conflicting_initials_name_both_bindings(self):
        text = (
            "version = 1\n"
            "[enc.1.turn]\nkind = 'cc-absolute'\ncc = 21\ninitial = 64\n"
            "[enc.2.turn.layers.2]\nkind = 'cc-absolute'\ncc = 21\ninitial = 0\n"
        )
        self.assertError(
            text,
            "CC 21 on channel 1",
            "enc.1.turn.initial",
            "enc.2.turn.layers.2.initial",
            start="enc.2.turn.layers.2.initial",
        )

    def test_matching_initials_or_other_channels_do_not_conflict(self):
        ok = (
            "version = 1\n"
            "[enc.1.turn]\nkind = 'cc-absolute'\ncc = 21\ninitial = 64\n"
            "[enc.2.turn]\nkind = 'cc-absolute'\ncc = 21\ninitial = 64\n"
            "[enc.3.turn]\nkind = 'cc-absolute'\ncc = 21\ninitial = 3\nchannel = 2\n"
        )
        parse_profile(ok)
        # An absolute dial that gives no start value agrees with any other.
        parse_profile(
            "version = 1\n[enc.1.turn]\nkind = 'cc-absolute'\ncc = 21\ninitial = 5\n"
            "[enc.2.turn]\nkind = 'cc-absolute'\ncc = 21\n"
        )

    def test_default_channel_counts_for_initial_conflicts(self):
        text = (
            "version = 1\n[midi]\nchannel = 2\n"
            "[enc.1.turn]\nkind = 'cc-absolute'\ncc = 21\ninitial = 1\nchannel = 2\n"
            "[enc.2.turn]\nkind = 'cc-absolute'\ncc = 21\ninitial = 9\n"
        )
        self.assertError(text, "channel 2", start="enc.2.turn.initial")


class RoundTripTests(unittest.TestCase):
    def test_every_kind_round_trips(self):
        self.assertEqual(validate(EVERY_KIND), [])
        self.assertEqual(parse_profile(dumps_profile(EVERY_KIND)), EVERY_KIND)

    def test_design_example_and_default_round_trip(self):
        for p in (parse_profile(DESIGN_EXAMPLE), load_profile()):
            self.assertEqual(parse_profile(dumps_profile(p)), p)

    def test_empty_profile_round_trips(self):
        p = Profile()
        self.assertEqual(parse_profile(dumps_profile(p)), p)

    def test_defaults_are_left_out_but_required_fields_stay(self):
        text = dumps_profile(
            Profile(controls={"key.1": Note(note=36), "key.2": CcStep(cc=1, step=-1)})
        )
        self.assertIn('[key.1]\nkind = "note"\nnote = 36\n', text)
        self.assertNotIn("velocity", text)
        self.assertNotIn("channel = null", text)
        self.assertIn('[key.2]\nkind = "cc-step"\ncc = 1\nstep = -1\n', text)
        self.assertNotIn("ease-ms", text)

    def test_cc_momentary_rise_and_fall_are_separate(self):
        p = parse_profile(
            'version = 1\n[key.1]\nkind = "cc-momentary"\ncc = 1\nrise-ms = 50\n'
        )
        self.assertEqual(p.controls["key.1"], CcMomentary(cc=1, rise_ms=50, fall_ms=0))
        text = dumps_profile(p)
        self.assertIn("rise-ms = 50", text)
        self.assertNotIn("fall-ms", text)
        self.assertEqual(parse_profile(text), p)

    def test_fixed_order_and_one_line_arrays(self):
        text = dumps_profile(EVERY_KIND)
        order = [
            "version = 1",
            "[midi]",
            "[pad]",
            "[layers]",
            "[lighting]",
            "[key.1]",
            "[key.2.layers.1]",
            "[key.2.layers.3]",
            "[key.3]",
            "[key.7]",
            "[enc.1.push.layers.2]",
            "[enc.1.turn]",
            "[enc.2.turn.layers.1]",
            "[enc.3.turn]",
        ]
        positions = [text.index(item) for item in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('names = ["Drums", "", "Mixer"]', text)
        self.assertIn("color = [10, 200, 255]", text)
        self.assertTrue(text.startswith("# glra-midi profile"))

    def test_trailing_empty_names_are_not_written(self):
        p = Profile(layer_names=("A", "", "", ""))
        text = dumps_profile(p)
        self.assertIn('names = ["A"]', text)
        self.assertEqual(parse_profile(text), p)
        self.assertNotIn("names =", dumps_profile(Profile()))

    def test_awkward_strings_survive(self):
        p = Profile(port='Pad "A", \\ é', layer_names=('He said "hi"', "a, b", "", ""))
        self.assertEqual(parse_profile(dumps_profile(p)), p)

    def test_dump_refuses_an_invalid_profile(self):
        bad = Profile(controls={"key.1": LayerSet(layer=7)})
        with self.assertRaises(ProfileError) as ctx:
            dumps_profile(bad)
        self.assertIn("key.1.layer", str(ctx.exception))


class FileTests(unittest.TestCase):
    def test_dump_and_load(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sub" / "profile.toml"  # the directory doesn't exist yet
            dump_profile(EVERY_KIND, path)
            self.assertEqual(load_profile(path), EVERY_KIND)
            self.assertEqual(os.listdir(path.parent), ["profile.toml"])  # no temp file left

    def test_dump_replaces_an_existing_file_and_keeps_its_mode(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "profile.toml"
            path.write_text("old")
            path.chmod(0o640)
            dump_profile(Profile(), path)
            self.assertEqual(load_profile(path), Profile())
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)

    def test_a_failed_dump_leaves_the_old_file_and_no_temp_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "profile.toml"
            path.write_text("keep me")
            with self.assertRaises(ProfileError):
                dump_profile(Profile(controls={"key.1": LayerSet(layer=9)}), path)
            self.assertEqual(path.read_text(), "keep me")
            self.assertEqual(os.listdir(d), ["profile.toml"])

    def test_missing_file(self):
        with self.assertRaises(ProfileError) as ctx:
            load_profile("/nonexistent/p.toml")
        self.assertIn("/nonexistent/p.toml", str(ctx.exception))

    def test_error_from_file_names_the_file_and_key(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.toml"
            path.write_text("version = 1\n[key.1]\nkind = 'note'\nnote = 999\n")
            with self.assertRaises(ProfileError) as ctx:
                load_profile(path)
            self.assertIn("bad.toml", str(ctx.exception))
            self.assertIn("key.1.note", str(ctx.exception))

    def test_paths(self):
        self.assertTrue(default_profile_path().is_file())
        base = Path("/Users/someone/Library/Application Support/glra-midi")
        self.assertEqual(app_dir("/Users/someone"), base)
        self.assertEqual(profiles_dir("/Users/someone"), base / "profiles")
        self.assertEqual(profile_path("drums", "/Users/someone"), base / "profiles" / "drums.toml")
        self.assertEqual(app_dir().name, "glra-midi")


class AppDirMigrationTests(unittest.TestCase):
    """The pre-rename `glra-osc` folder moves to `glra-midi` once (Bob, 2026-11-13, Q9)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        self.support = self.home / "Library" / "Application Support"
        self.old = self.support / "glra-osc"
        self.new = self.support / "glra-midi"

    def fill_old(self):
        (self.old / "profiles").mkdir(parents=True)
        (self.old / "profiles" / "drums.toml").write_text("version = 1\n")
        (self.old / "current").write_text("drums\n")
        (self.old / "backups").mkdir()
        (self.old / "backups" / "b.json").write_text("{}")
        (self.old / "logs").mkdir()
        (self.old / "logs" / "audit.log").write_text("x\n")

    def test_the_new_folder_is_named_glra_midi(self):
        self.assertEqual(app_dir(self.home), self.new)

    def test_moves_everything_and_says_so_once(self):
        self.fill_old()
        message = migrate_app_dir(self.home)
        self.assertIn(str(self.old), message)
        self.assertIn(str(self.new), message)
        self.assertFalse(self.old.exists())
        self.assertEqual((self.new / "current").read_text(), "drums\n")
        for rel in ("profiles/drums.toml", "backups/b.json", "logs/audit.log"):
            self.assertTrue((self.new / rel).is_file(), rel)
        self.assertIsNone(migrate_app_dir(self.home))  # second start: nothing to say
        self.assertEqual(current_profile_path(self.home), self.new / "profiles" / "drums.toml")

    def test_no_old_folder_does_nothing(self):
        self.assertIsNone(migrate_app_dir(self.home))
        self.assertFalse(self.new.exists())

    def test_an_existing_new_folder_is_left_alone_and_the_old_one_kept(self):
        self.fill_old()
        self.new.mkdir(parents=True)
        (self.new / "current").write_text("default\n")
        self.assertIsNone(migrate_app_dir(self.home))
        self.assertEqual((self.new / "current").read_text(), "default\n")
        self.assertTrue((self.old / "current").is_file())

    def test_an_old_file_not_folder_is_ignored(self):
        self.support.mkdir(parents=True)
        self.old.write_text("not a folder")
        self.assertIsNone(migrate_app_dir(self.home))
        self.assertFalse(self.new.exists())

    def test_a_failed_move_is_reported_and_changes_nothing(self):
        self.fill_old()
        with mock.patch.object(Path, "rename", side_effect=OSError("busy")):
            message = migrate_app_dir(self.home)
        self.assertIn("could not move", message)
        self.assertTrue((self.old / "current").is_file())
        self.assertFalse(self.new.exists())

    def test_the_cli_moves_the_folder_on_a_command_but_not_on_version(self):
        import contextlib
        import io

        from glra_midi import cli, lighting

        old = Path.home() / "Library" / "Application Support" / "glra-osc"
        new = app_dir()
        self.assertTrue(str(old).startswith(tempfile.gettempdir().rstrip("/")))
        (old / "profiles").mkdir(parents=True)
        self.addCleanup(lambda: [__import__("shutil").rmtree(p, True) for p in (old, new)])
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            cli.main(["--version"])
        self.assertTrue(old.is_dir())
        with (
            mock.patch.object(lighting, "lights_command", return_value=0),
            contextlib.redirect_stderr(err),
        ):
            self.assertEqual(cli.main(["lights"]), 0)
            self.assertEqual(cli.main(["lights"]), 0)
        self.assertFalse(old.exists())
        self.assertTrue((new / "profiles").is_dir())
        self.assertEqual(err.getvalue().count("moved"), 1)

    def test_the_default_home_is_the_test_home(self):
        # tests/__init__.py points HOME at a throwaway folder; this guards Bob's real one.
        self.assertTrue(str(Path.home()).startswith(tempfile.gettempdir().rstrip("/")))


class ProfileFolderTests(unittest.TestCase):
    """The profiles folder and the `current` pointer (design 2; Bob, 2026-11-13, Q7)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.current = app_dir(self.home) / "current"

    def add(self, name, text="version = 1\n"):
        path = profile_path(name, self.home)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def point(self, text):
        self.current.parent.mkdir(parents=True, exist_ok=True)
        self.current.write_text(text)

    def test_a_fresh_home_gets_default_from_the_shipped_profile(self):
        path = current_profile_path(self.home)
        self.assertEqual(path, profiles_dir(self.home) / "default.toml")
        self.assertEqual(path.read_text(), default_profile_path().read_text())
        self.assertEqual(self.current.read_text().strip(), "default")
        self.assertEqual(load_profile(path), load_profile())

    def test_follows_the_pointer(self):
        self.add("default")
        drums = self.add("drums")
        self.point("drums\n")
        self.assertEqual(current_profile_path(self.home), drums)

    def test_every_fallback_lands_on_default_and_keeps_the_pointer(self):
        for pointer in ("", "  \n", "nope\n", "../x\n", ".hidden\n", "a/b\n"):
            with self.subTest(pointer=pointer):
                self.point(pointer)
                path = current_profile_path(self.home)
                self.assertEqual(path, profiles_dir(self.home) / "default.toml")
                self.assertTrue(path.is_file())
                self.assertEqual(self.current.read_text(), pointer)  # never rewritten

    def test_an_existing_default_is_never_overwritten(self):
        default = self.add("default", "version = 1\n# mine\n")
        self.assertEqual(current_profile_path(self.home), default)
        self.assertEqual(default.read_text(), "version = 1\n# mine\n")
        self.assertEqual(self.current.read_text().strip(), "default")  # missing pointer written

    def test_a_pointer_that_exists_is_never_rewritten(self):
        self.add("default")
        self.point("gone\n")
        current_profile_path(self.home)
        self.assertEqual(self.current.read_text(), "gone\n")

    def test_set_current(self):
        self.add("drums")
        set_current("drums", self.home)
        self.assertEqual(self.current.read_text(), "drums\n")
        self.assertEqual(current_profile_path(self.home), profile_path("drums", self.home))

    def test_set_current_needs_an_existing_profile(self):
        self.add("default")
        with self.assertRaises(ProfileError):
            set_current("missing", self.home)
        self.assertFalse(self.current.exists())

    def test_set_current_leaves_no_temp_file(self):
        self.add("drums")
        set_current("drums", self.home)
        self.assertEqual(sorted(os.listdir(app_dir(self.home))), ["current", "profiles"])

    def test_names(self):
        for name in ("drums", "my drums 2", "Über", "a.b", "x" * 100):
            self.assertEqual(check_profile_name(name), name)
        for name in ("", ".x", "a/b", "a\\b", "a\0b", "x" * 101, None, 5):
            with self.subTest(name=name):
                with self.assertRaises(ProfileError):
                    check_profile_name(name)
        with self.assertRaises(ProfileError):
            set_current("../escape", self.home)


class DefaultProfileTests(unittest.TestCase):
    """Bob, 2026-11-13, Q3 (design 2.7)."""

    def setUp(self):
        self.p = load_profile()

    def test_shape(self):
        p = self.p
        self.assertEqual((p.port, p.channel, p.layer_count, p.lighting), ("GLRA K16", 1, 3, None))
        self.assertEqual(p.layer_names, ("",) * 3)
        self.assertEqual(validate(p), [])

    def test_keys_are_momentary_notes_on_the_layers_channel(self):
        for layer in range(1, 4):
            for key in range(1, 17):
                self.assertEqual(
                    self.p.action(f"key.{key}", layer),
                    Note(note=35 + key, channel=layer),
                )

    def test_dial_pushes_select_layers(self):
        for n in (1, 2, 3):
            self.assertEqual(self.p.controls[f"enc.{n}.push"], LayerSet(layer=n))

    def test_left_and_middle_dials_are_per_layer_relative(self):
        for n in (1, 2):
            for layer in range(1, 4):
                self.assertEqual(
                    self.p.action(f"enc.{n}.turn", layer), CcRelative(cc=15 + n, channel=layer)
                )

    def test_right_dial_is_one_global_absolute_cc(self):
        self.assertEqual(
            self.p.controls["enc.3.turn"], CcAbsolute(cc=18, channel=1, initial=64)
        )
        self.assertEqual(len(self.p.controls), 16 + 6)


class NoLegacyTests(unittest.TestCase):
    """Old mapping files stopped loading (Bob, 2026-11-13: "we can hard break")."""

    def test_a_file_without_version_is_an_error(self):
        for text in ("", "[key.1]\nnote = 36\n"):
            with self.assertRaises(ProfileError) as ctx:
                parse_profile(text, source="m.toml")
            message = str(ctx.exception)
            self.assertTrue(message.startswith("m.toml: version: required"), message)

    def test_an_old_style_mapping_doesnt_load(self):
        old = '[midi]\nchannel = 1\n\n[keys]\n1 = { note = 36 }\n'
        with self.assertRaises(ProfileError) as ctx:
            parse_profile(old, source="old.toml")
        self.assertIn("version", str(ctx.exception))


class ValidateTests(unittest.TestCase):
    def test_collects_every_problem(self):
        p = Profile(
            channel=17,
            layer_count=2,
            layer_names=("", ""),
            controls={
                "key.1": LayerSet(layer=3),
                "key.2": PerLayer.of({1: LayerInc()}),
                "key.3": Note(note=500),
                "enc.1.turn": LayerInc(),
                "enc.9.turn": CcRelative(cc=1),
                "enc.2.turn": CcAbsolute(cc=5, initial=1),
                "enc.3.turn": CcAbsolute(cc=5, initial=2),
            },
        )
        messages = [problem.message for problem in validate(p)]
        starts = [m.split(":")[0] for m in messages]
        for path in (
            "midi.channel",
            "key.1.layer",
            "key.2.layers.1",
            "key.3.note",
            "enc.1.turn.kind",
            "enc.9.turn",
            "enc.3.turn.initial",
        ):
            self.assertIn(path, starts, messages)
        self.assertEqual({pr.control for pr in validate(p)} - {None}, {
            "key.1", "key.2", "key.3", "enc.1.turn", "enc.9.turn", "enc.3.turn"
        })

    def test_layer_names_must_match_count(self):
        problems = validate(Profile(layer_count=4, layer_names=("a",)))
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].message.startswith("layers.names"))

    def test_a_clean_profile_has_none(self):
        self.assertEqual(validate(EVERY_KIND), [])


class EditEventTests(unittest.TestCase):
    def setUp(self):
        self.p = parse_profile(DESIGN_EXAMPLE)

    def test_set_event_on_an_empty_control(self):
        edit = set_event(self.p, "key.5", 2, Note(note=50))
        self.assertEqual(edit.profile.controls["key.5"], PerLayer.of({2: Note(note=50)}))
        self.assertEqual(edit.discarded, ())
        self.assertNotIn("key.5", self.p.controls)  # the old profile is untouched

    def test_set_event_on_the_global_tab_makes_a_global_event(self):
        edit = set_event(self.p, "key.5", None, Note(note=50))
        self.assertEqual(edit.profile.controls["key.5"], Note(note=50))

    def test_set_event_replaces_a_global_event_whichever_layer_is_shown(self):
        edit = set_event(self.p, "key.1", 3, Note(note=99, velocity=5))
        self.assertEqual(edit.profile.controls["key.1"], Note(note=99, velocity=5))
        self.assertEqual(edit.discarded, ())

    def test_set_event_on_a_per_layer_control_edits_one_layer(self):
        edit = set_event(self.p, "key.2", 3, CcSet(cc=1, value=2))
        events = edit.profile.controls["key.2"].as_dict()
        self.assertEqual(sorted(events), [1, 2, 3])
        self.assertEqual(events[3], CcSet(cc=1, value=2))
        self.assertEqual(events[1], Note(note=37, mode="latch"))
        replaced = set_event(self.p, "key.2", 1, Note(note=1))
        self.assertEqual(replaced.discarded, ())

    def test_set_event_on_a_per_layer_control_from_the_global_tab_is_an_error(self):
        with self.assertRaises(ProfileError) as ctx:
            set_event(self.p, "key.2", None, Note(note=1))
        self.assertTrue(str(ctx.exception).startswith("key.2"))

    def test_set_event_over_a_layer_key_reports_it(self):
        edit = set_event(self.p, "key.13", 2, Note(note=1))
        self.assertEqual(edit.profile.controls["key.13"], PerLayer.of({2: Note(note=1)}))
        self.assertEqual([(d.control, d.layer, d.action) for d in edit.discarded], [("key.13", None, LayerSet(layer=1))])
        glob = set_event(self.p, "key.13", None, Note(note=1))
        self.assertEqual(glob.profile.controls["key.13"], Note(note=1))

    def test_set_event_checks_kind_and_fields(self):
        with self.assertRaises(ProfileError):
            set_event(self.p, "key.5", 1, LayerInc())  # use set_layer_key
        with self.assertRaises(ProfileError):
            set_event(self.p, "key.5", 1, CcRelative(cc=1))  # a turn kind on a press
        with self.assertRaises(ProfileError):
            set_event(self.p, "enc.1.turn", 1, Note(note=1))
        with self.assertRaises(ProfileError):
            set_event(self.p, "key.5", 1, Note(note=200))
        with self.assertRaises(ProfileError):
            set_event(self.p, "key.5", 7, Note(note=1))  # layer 7 of 4
        with self.assertRaises(ProfileError):
            set_event(self.p, "key.17", 1, Note(note=1))
        set_event(self.p, "enc.1.turn", 1, CcRelative(cc=1))

    def test_clear_one_layer_of_a_per_layer_control(self):
        edit = clear_event(self.p, "key.2", 1)
        self.assertEqual(sorted(edit.profile.controls["key.2"].as_dict()), [2])
        self.assertEqual([(d.layer, d.action) for d in edit.discarded], [(1, Note(note=37, mode="latch"))])

    def test_clearing_the_last_layer_removes_the_control(self):
        edit = clear_event(self.p, "key.4", 1)
        self.assertNotIn("key.4", edit.profile.controls)

    def test_clearing_an_empty_layer_changes_nothing(self):
        edit = clear_event(self.p, "key.2", 3)
        self.assertEqual(edit.profile, self.p)
        self.assertEqual(edit.discarded, ())

    def test_clear_global_or_layer_key_clears_it_everywhere(self):
        for name in ("key.1", "key.13", "enc.1.push"):
            edit = clear_event(self.p, name, 2)
            self.assertNotIn(name, edit.profile.controls)
            self.assertEqual(len(edit.discarded), 1)

    def test_clear_per_layer_control_from_the_global_tab_clears_all(self):
        edit = clear_event(self.p, "key.2")
        self.assertNotIn("key.2", edit.profile.controls)
        self.assertEqual(len(edit.discarded), 2)

    def test_clear_an_absent_control(self):
        edit = clear_event(self.p, "key.16", 1)
        self.assertEqual((edit.profile, edit.discarded), (self.p, ()))


class EditShapeTests(unittest.TestCase):
    def setUp(self):
        self.p = parse_profile(DESIGN_EXAMPLE)

    def test_make_global_from_a_layer_keeps_that_layers_event_and_reports_different_others(self):
        edit = make_global(self.p, "key.2", 2)
        self.assertEqual(edit.profile.controls["key.2"], self.p.action("key.2", 2))
        self.assertEqual([(d.layer, d.action) for d in edit.discarded], [(1, Note(note=37, mode="latch"))])

    def test_make_global_from_the_global_tab_takes_the_lowest_layer(self):
        edit = make_global(self.p, "key.2")
        self.assertEqual(edit.profile.controls["key.2"], Note(note=37, mode="latch"))
        self.assertEqual([d.layer for d in edit.discarded], [2])

    def test_make_global_discards_nothing_when_the_other_layers_agree(self):
        same = Note(note=5)
        p = Profile(controls={"key.1": PerLayer.of({1: same, 2: same, 4: same})})
        edit = make_global(p, "key.1", 2)
        self.assertEqual(edit.profile.controls["key.1"], same)
        self.assertEqual(edit.discarded, ())

    def test_make_global_needs_an_event_on_the_layer(self):
        with self.assertRaises(ProfileError):
            make_global(self.p, "key.2", 3)
        with self.assertRaises(ProfileError):
            make_global(self.p, "key.16", 1)

    def test_make_global_leaves_global_and_layer_keys_alone(self):
        for name in ("key.1", "key.13"):
            self.assertEqual(make_global(self.p, name, 1).profile, self.p)

    def test_make_per_layer_copies_the_event_to_every_layer(self):
        edit = make_per_layer(self.p, "key.1")
        self.assertEqual(
            edit.profile.controls["key.1"], PerLayer.of({n: Note(note=36, velocity=110) for n in (1, 2, 3, 4)})
        )
        for layer in (1, 2, 3, 4):  # nothing changes in play
            self.assertEqual(edit.profile.action("key.1", layer), self.p.action("key.1", layer))
        self.assertEqual(edit.discarded, ())
        self.assertEqual(validate(edit.profile), [])

    def test_make_per_layer_errors(self):
        self.assertEqual(make_per_layer(self.p, "key.2").profile, self.p)
        with self.assertRaises(ProfileError):
            make_per_layer(self.p, "key.13")  # a layer key stays global
        with self.assertRaises(ProfileError):
            make_per_layer(self.p, "key.16")

    def test_global_then_per_layer_then_global_round_trips(self):
        there = make_per_layer(self.p, "key.1").profile
        back = make_global(there, "key.1", 3)
        self.assertEqual(back.profile, self.p)
        self.assertEqual(back.discarded, ())

    def test_set_layer_key_discards_every_event_it_replaces(self):
        edit = set_layer_key(self.p, "key.2", LayerInc())
        self.assertEqual(edit.profile.controls["key.2"], LayerInc())
        self.assertEqual(sorted(d.layer for d in edit.discarded), [1, 2])
        glob = set_layer_key(self.p, "key.1", LayerDec())
        self.assertEqual([d.layer for d in glob.discarded], [None])
        empty = set_layer_key(self.p, "key.16", LayerSet(layer=2))
        self.assertEqual((empty.profile.controls["key.16"], empty.discarded), (LayerSet(layer=2), ()))

    def test_changing_one_layer_key_to_another_loses_nothing(self):
        edit = set_layer_key(self.p, "key.13", LayerSet(layer=3))
        self.assertEqual((edit.profile.controls["key.13"], edit.discarded), (LayerSet(layer=3), ()))

    def test_set_layer_key_errors(self):
        with self.assertRaises(ProfileError):
            set_layer_key(self.p, "enc.1.turn", LayerInc())
        with self.assertRaises(ProfileError):
            set_layer_key(self.p, "key.1", LayerSet(layer=5))
        with self.assertRaises(ProfileError):
            set_layer_key(self.p, "key.1", Note(note=1))


class EditLayerTests(unittest.TestCase):
    def setUp(self):
        self.p = parse_profile(DESIGN_EXAMPLE)  # 4 layers; key.2 on 1 and 2; key.4/8 and enc.2.turn on 1, 2

    def test_add_layer(self):
        edit = add_layer(self.p, "Fx")
        self.assertEqual((edit.profile.layer_count, edit.profile.layer_names[-1]), (5, "Fx"))
        self.assertEqual(edit.profile.controls, self.p.controls)
        self.assertEqual(validate(edit.profile), [])
        self.assertEqual(parse_profile(dumps_profile(edit.profile)), edit.profile)

    def test_add_layer_stops_at_eight(self):
        p = self.p
        for _ in range(4):
            p = add_layer(p).profile
        self.assertEqual(p.layer_count, 8)
        with self.assertRaises(ProfileError):
            add_layer(p)

    def test_remove_layer_drops_its_events_and_renumbers_the_ones_above(self):
        p = Profile(
            layer_names=("A", "B", "C", "D"),
            controls={
                "key.1": PerLayer.of({1: Note(note=1), 2: Note(note=2), 4: Note(note=4)}),
                "key.2": PerLayer.of({2: Note(note=22)}),
                "key.3": Note(note=3),
                "key.4": LayerInc(),
            },
        )
        edit = remove_layer(p, 2)
        q = edit.profile
        self.assertEqual((q.layer_count, q.layer_names), (3, ("A", "C", "D")))
        self.assertEqual(q.controls["key.1"], PerLayer.of({1: Note(note=1), 3: Note(note=4)}))
        self.assertNotIn("key.2", q.controls)  # left with nothing
        self.assertEqual((q.controls["key.3"], q.controls["key.4"]), (Note(note=3), LayerInc()))
        self.assertEqual(
            sorted((d.control, d.layer, d.action) for d in edit.discarded),
            [("key.1", 2, Note(note=2)), ("key.2", 2, Note(note=22))],
        )
        self.assertEqual(validate(q), [])
        self.assertEqual(parse_profile(dumps_profile(q)), q)

    def test_remove_first_and_last_layer(self):
        p = Profile(layer_count=3, layer_names=("", "", ""), controls={"key.1": PerLayer.of({1: Note(note=1), 3: Note(note=3)})})
        self.assertEqual(remove_layer(p, 1).profile.controls["key.1"], PerLayer.of({2: Note(note=3)}))
        self.assertEqual(remove_layer(p, 3).profile.controls["key.1"], PerLayer.of({1: Note(note=1)}))

    def test_remove_layer_renumbers_layer_keys_above_it(self):
        p = Profile(
            layer_count=4,
            layer_names=("",) * 4,
            controls={
                "key.1": LayerSet(layer=1),
                "key.2": LayerSet(layer=3),
                "key.3": LayerSet(layer=4),
                "key.4": LayerInc(),
            },
        )
        q = remove_layer(p, 2).profile
        self.assertEqual(
            [q.controls[n] for n in ("key.1", "key.2", "key.3", "key.4")],
            [LayerSet(layer=1), LayerSet(layer=2), LayerSet(layer=3), LayerInc()],
        )
        self.assertEqual(validate(q), [])
        self.assertEqual(parse_profile(dumps_profile(q)), q)

    def test_remove_layer_flags_layer_keys_that_pointed_at_it(self):
        p = Profile(
            layer_count=3,
            layer_names=("",) * 3,
            controls={"key.1": LayerSet(layer=2), "key.2": LayerSet(layer=3)},
        )
        q = remove_layer(p, 2).profile
        self.assertEqual(q.controls["key.1"], LayerSet(layer=NO_LAYER))
        self.assertEqual(q.controls["key.2"], LayerSet(layer=2))  # followed its layer
        problems = validate(q)
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0].control, "key.1")
        self.assertIn("key.1.layer: the layer it pointed at was removed", problems[0].message)

    def test_remove_layer_applies_the_same_rule_to_layer_sets_inside_per_layer_controls(self):
        # The parser and editors keep layer keys out of per-layer controls, but a profile built
        # in code can hold one; removing a layer must not silently retarget it either.
        p = Profile(
            layer_count=4,
            layer_names=("",) * 4,
            controls={
                "key.1": PerLayer.of({2: LayerSet(layer=3), 3: LayerSet(layer=2), 4: LayerSet(layer=1)}),
            },
        )
        q = remove_layer(p, 2).profile  # layer 2's event goes; 3 -> 2, 4 -> 3
        self.assertEqual(
            q.controls["key.1"], PerLayer.of({2: LayerSet(layer=NO_LAYER), 3: LayerSet(layer=1)})
        )
        flagged = [x for x in validate(q) if "was removed" in x.message]
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0].control, "key.1")
        self.assertTrue(flagged[0].message.startswith("key.1.layers.2.layer: the layer it pointed at was removed"))
        r = remove_layer(p, 1).profile  # a key above the removed layer moves down with it
        self.assertEqual(
            r.controls["key.1"],
            PerLayer.of({1: LayerSet(layer=2), 2: LayerSet(layer=1), 3: LayerSet(layer=NO_LAYER)}),
        )

    def test_remove_layer_still_flags_a_key_already_past_the_count(self):
        p = Profile(layer_count=3, layer_names=("",) * 3, controls={"key.1": LayerSet(layer=5)})
        q = remove_layer(p, 1).profile
        self.assertEqual(q.controls["key.1"], LayerSet(layer=4))
        self.assertIn("layer 4 doesn't exist (count = 2)", validate(q)[0].message)

    def test_at_least_one_layer_remains(self):
        p = Profile(layer_count=1, layer_names=("",))
        with self.assertRaises(ProfileError):
            remove_layer(p, 1)

    def test_remove_a_layer_that_does_not_exist(self):
        with self.assertRaises(ProfileError):
            remove_layer(self.p, 5)
        with self.assertRaises(ProfileError):
            remove_layer(self.p, None)

    def test_rename_layer(self):
        edit = rename_layer(self.p, 3, "Pads")
        self.assertEqual(edit.profile.layer_names, ("Drums", "Synth", "Pads", "Mixer"))
        self.assertEqual(rename_layer(edit.profile, 3, "").profile.layer_names[2], "")
        with self.assertRaises(ProfileError):
            rename_layer(self.p, 5, "x")


class ControlNameTests(unittest.TestCase):
    def test_canonical_names(self):
        self.assertEqual(len(CONTROL_NAMES), 22)
        self.assertEqual(CONTROL_NAMES[0], "key.1")
        self.assertEqual(CONTROL_NAMES[16:18], ("enc.1.push", "enc.1.turn"))


class FieldAccessTests(unittest.TestCase):
    def test_specs_describe_the_fields_the_parser_checks(self):
        specs = {s["key"]: s for s in profile.event_field_specs("cc-step")}
        self.assertEqual((specs["step"]["lo"], specs["step"]["hi"], specs["step"]["nonzero"]), (-127, 127, True))
        self.assertEqual(specs["curve"]["choices"], profile.CURVES)
        self.assertTrue(specs["cc"]["required"])
        self.assertFalse(specs["ease-ms"]["required"])
        self.assertIsNone({s["key"]: s for s in profile.event_field_specs("note")}["channel"]["default"])

    def test_fields_round_trip_through_an_event(self):
        event = profile.CcMomentary(cc=20, low=10, high=120, rise_ms=5, curve="ease-in", channel=3)
        fields = profile.event_fields(event)
        self.assertEqual(fields["rise-ms"], 5)
        self.assertEqual(profile.event_from_fields("cc-momentary", fields), event)

    def test_event_from_fields_uses_the_parsers_errors(self):
        with self.assertRaisesRegex(ProfileError, r"^k\.cc: expected an integer 0\.\.127, got 300"):
            profile.event_from_fields("cc-set", {"cc": 300, "value": 1}, path="k")
        with self.assertRaisesRegex(ProfileError, "value: required"):
            profile.event_from_fields("cc-set", {"cc": 3})
        with self.assertRaisesRegex(ProfileError, "kind"):
            profile.event_from_fields("nonsense", {})


if __name__ == "__main__":
    unittest.main()
