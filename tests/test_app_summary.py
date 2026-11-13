# SPDX-License-Identifier: GPL-3.0-only

import subprocess
import sys
import unittest

from glra_midi.app import summary
from glra_midi.profile import (
    CcAbsolute,
    CcMomentary,
    CcRelative,
    CcSet,
    CcStep,
    LayerDec,
    LayerInc,
    LayerSet,
    NO_LAYER,
    Note,
    PerLayer,
    Profile,
)

MINUS = "\N{MINUS SIGN}"


class NoteNameTests(unittest.TestCase):
    def test_c1_is_36_and_middle_c_is_c3(self):
        self.assertEqual(summary.note_name(36), "C1")
        self.assertEqual(summary.note_name(60), "C3")
        self.assertEqual(summary.note_name(61), "C#3")
        self.assertEqual(summary.note_name(0), "C-2")
        self.assertEqual(summary.note_name(127), "G8")


class SummarizeTests(unittest.TestCase):
    def test_note_momentary_and_latch(self):
        self.assertEqual(summary.summarize(Note(36, 110)), ("Note C1", "vel 110"))
        self.assertEqual(
            summary.summarize(Note(37, mode="latch")), ("Note C#1", "latch · vel 127")
        )

    def test_note_with_names_off_shows_the_number(self):
        self.assertEqual(summary.summarize(Note(36, 110), note_names=False), ("Note 36", "vel 110"))

    def test_cc_momentary(self):
        event = CcMomentary(20, low=10, high=120, rise_ms=250, fall_ms=600, curve="ease-out")
        self.assertEqual(summary.summarize(event), ("CC20 10↔120", "↑250 ↓600 ms ease-out"))

    def test_cc_momentary_latch_and_blank_line_when_no_times(self):
        latch = CcMomentary(20, rise_ms=100, fall_ms=0, mode="latch")
        self.assertEqual(summary.summarize(latch), ("CC20 0↔127", "↑100 ↓0 ms linear · latch"))
        self.assertEqual(summary.summarize(CcMomentary(20)), ("CC20 0↔127", ""))
        self.assertEqual(summary.summarize(CcMomentary(20, mode="latch")), ("CC20 0↔127", "latch"))

    def test_cc_set(self):
        self.assertEqual(summary.summarize(CcSet(21, 64)), ("CC21 = 64", ""))

    def test_cc_step_signs_and_time(self):
        self.assertEqual(summary.summarize(CcStep(21, 8, ease_ms=120)), ("CC21 +8", "120 ms"))
        self.assertEqual(summary.summarize(CcStep(21, -8)), (f"CC21 {MINUS}8", ""))

    def test_layer_keys(self):
        self.assertEqual(summary.summarize(LayerSet(1), layer_names=("Drums", "")), ("→ L1", "Drums"))
        self.assertEqual(summary.summarize(LayerSet(2), layer_names=("Drums", "")), ("→ L2", ""))
        self.assertEqual(summary.summarize(LayerInc()), ("L+1 ▶", "wraps"))
        self.assertEqual(summary.summarize(LayerDec()), (f"◀ L{MINUS}1", "wraps"))

    def test_turns(self):
        self.assertEqual(summary.summarize(CcRelative(16)), ("CC16 rel", "2's"))
        self.assertEqual(
            summary.summarize(CcRelative(17, "binary-offset")), ("CC17 rel", "offset")
        )
        self.assertEqual(summary.summarize(CcRelative(17, "signed-bit")), ("CC17 rel", "sign"))
        self.assertEqual(summary.summarize(CcAbsolute(21, step=2)), ("CC21 abs", "step 2"))

    def test_channel_shows_only_when_it_differs_from_the_default(self):
        self.assertEqual(summary.summarize(CcSet(21, 64, channel=1), 1), ("CC21 = 64", ""))
        self.assertEqual(summary.summarize(CcSet(21, 64, channel=10), 1), ("CC21 = 64", "ch 10"))
        self.assertEqual(summary.summarize(CcSet(21, 64, channel=1), 3), ("CC21 = 64", "ch 1"))
        self.assertEqual(
            summary.summarize(Note(36, channel=2)), ("Note C1", "vel 127 · ch 2")
        )
        self.assertEqual(summary.summarize(CcRelative(16, channel=4)), ("CC16 rel", "2's · ch 4"))

    def test_rejects_what_is_not_an_event(self):
        with self.assertRaises(TypeError):
            summary.summarize("note")


class TileInfoTests(unittest.TestCase):
    def setUp(self):
        self.profile = Profile(
            layer_count=4,
            layer_names=("Drums", "", "", ""),
            controls={
                "key.1": Note(36),
                "key.2": PerLayer.of({1: Note(37), 3: CcSet(20, 5)}),
                "key.13": LayerSet(2),
            },
        )

    def tile(self, control, tab):
        return summary.tile_info(self.profile, control, tab)

    def test_empty(self):
        info = self.tile("key.5", 1)
        self.assertEqual((info["state"], info["badge"], info["line1"]), ("empty", "", "—"))

    def test_global_event_reads_the_same_on_every_tab_with_a_g_badge(self):
        on_layer, on_global = self.tile("key.1", 2), self.tile("key.1", None)
        self.assertEqual(on_layer, on_global)
        self.assertEqual((on_layer["state"], on_layer["badge"]), ("global", "G"))
        self.assertEqual(on_layer["line1"], "Note C1")

    def test_layer_key_is_the_same_everywhere_with_a_lock(self):
        for tab in (None, 1, 4):
            info = self.tile("key.13", tab)
            self.assertEqual((info["state"], info["badge"]), ("layer-key", "🔒"))
            self.assertEqual(info["line1"], "→ L2")

    def test_per_layer_event_on_its_layer_is_a_plain_tile(self):
        info = self.tile("key.2", 3)
        self.assertEqual((info["state"], info["badge"], info["line1"]), ("layer", "", "CC20 = 5"))

    def test_per_layer_control_is_empty_on_a_layer_without_an_event(self):
        self.assertEqual(self.tile("key.2", 2)["state"], "empty")

    def test_per_layer_control_on_the_global_tab_is_dimmed_with_a_count(self):
        info = self.tile("key.2", None)
        self.assertEqual(info["state"], "per-layer")
        self.assertEqual((info["line1"], info["line2"]), ("per layer", "2 of 4"))
        self.assertEqual((info["layers_used"], info["layers_total"]), (2, 4))
        self.assertNotEqual(info["badge"], "")

    def test_every_state_has_its_own_look(self):
        looks = {
            (i["state"], i["badge"])
            for i in (
                self.tile("key.5", 1),
                self.tile("key.1", 1),
                self.tile("key.13", 1),
                self.tile("key.2", 1),
                self.tile("key.2", None),
            )
        }
        self.assertEqual(len(looks), 5)


class ImportTests(unittest.TestCase):
    def run_python(self, code):
        return subprocess.run(
            [sys.executable, "-I", "-c", code], capture_output=True, text=True, check=False
        )

    def test_cli_and_summary_import_without_qt(self):
        code = (
            "import sys; import glra_midi.cli, glra_midi.app, glra_midi.app.summary;"
            "sys.exit(1 if any(m.startswith(('PySide6', 'shiboken6')) for m in sys.modules) else 0)"
        )
        self.assertEqual(self.run_python(code).returncode, 0)

    def test_config_says_what_to_install_when_pyside6_is_missing(self):
        code = (
            "import sys; sys.modules['PySide6'] = None; sys.modules['shiboken6'] = None\n"
            "from glra_midi.cli import main\n"
            "sys.exit(main(['config']))"
        )
        result = self.run_python(code)
        self.assertEqual(result.returncode, 2)
        self.assertIn("glra-midi[gui]", result.stderr)



class RemovedLayerTests(unittest.TestCase):
    def test_a_layer_set_whose_layer_was_removed_reads_as_removed(self):
        self.assertEqual(summary.summarize(LayerSet(layer=NO_LAYER)), ("→ L?", "removed"))

    def test_tile_and_inspector_cope_with_it_global_or_per_layer(self):
        from glra_midi.app import inspector as insp

        p = Profile(
            layer_count=2,
            layer_names=("", ""),
            controls={"key.1": LayerSet(layer=NO_LAYER), "key.2": PerLayer.of({1: LayerSet(layer=NO_LAYER)})},
        )
        self.assertEqual(summary.tile_info(p, "key.1", 1)["line1"], "→ L?")
        self.assertEqual(summary.tile_info(p, "key.2", 1)["line1"], "→ L?")
        for control in ("key.1", "key.2"):
            d = insp.describe(p, control, 1)
            self.assertEqual((d["mode"], d["layerKey"]["layer"]), ("layer-key", NO_LAYER))

if __name__ == "__main__":
    unittest.main()
