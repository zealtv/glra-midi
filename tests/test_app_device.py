# SPDX-License-Identifier: GPL-3.0-only

"""The device panel: lighting, orientation, port and channel edit the profile; the one pad write
happens only on Apply. Every test uses a FakePad; none reaches the real device."""

import os
import tempfile
import threading
import time
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from . import qt_support  # noqa: F401 - skips this module without PySide6, sets up Qt
from .qt_support import forbid_real_device, make_home

from PySide6.QtCore import QCoreApplication  # noqa: E402

from glra_midi import lighting as lights
from glra_midi import profile as prof
from glra_midi.app import device as pads
from glra_midi.app import devicepanel as panel
from glra_midi.app.controller import Controller
from glra_midi.profile import Lighting

from .test_lighting import FakePad as ReaderFake  # a fake at the Reader level

BREATHING = Lighting(mode=2, brightness=4, speed=2, color=(0, 255, 255))  # the demo profile's


class PanelLogicTests(unittest.TestCase):
    """devicepanel.py: pure edits."""

    def test_the_selector_offers_leave_as_it_is_and_all_thirteen_modes(self):
        choices = panel.mode_choices()
        self.assertEqual(choices[0], {"value": -1, "label": "Leave as it is"})
        self.assertEqual([c["value"] for c in choices[1:]], list(range(13)))

    def test_choosing_a_mode_from_nothing_uses_the_defaults(self):
        self.assertEqual(panel.with_mode(None, 3), Lighting(mode=3, brightness=4, speed=2))

    def test_leave_as_it_is_removes_the_section(self):
        self.assertIsNone(panel.with_mode(BREATHING, panel.NOT_SET))

    def test_a_colour_goes_when_the_new_mode_takes_none(self):
        self.assertIsNone(panel.with_mode(BREATHING, 3).color)
        self.assertEqual(panel.with_mode(BREATHING, 6).color, (0, 255, 255))

    def test_levels_are_limited_to_0_to_4(self):
        self.assertEqual(panel.with_level(BREATHING, "speed", 0).speed, 0)
        for bad in (-1, 5):
            with self.assertRaises(lights.LightingError):
                panel.with_level(BREATHING, "brightness", bad)

    def test_colour_on_off_and_bytes(self):
        steady = panel.with_mode(None, 1)
        on = panel.with_color(steady, True)
        self.assertEqual(on.color, panel.DEFAULT_COLOR)
        self.assertIsNone(panel.with_color(on, False).color)
        self.assertEqual(panel.with_hsv(on, 0, 100).color, (100, 255, 255))
        with self.assertRaises(lights.LightingError):
            panel.with_hsv(on, 0, 256)
        with self.assertRaises(lights.LightingError):
            panel.with_color(panel.with_mode(None, 3), True)  # Spectrum takes no colour

    def test_describe_shows_only_the_fields_a_mode_reads(self):
        spectrum = panel.describe_lighting(panel.with_mode(None, 3))
        self.assertFalse(spectrum["color"]["shown"])
        steady = panel.describe_lighting(panel.with_mode(None, 1))
        self.assertTrue(steady["brightness"]["shown"])
        self.assertFalse(steady["speed"]["shown"])
        off = panel.describe_lighting(panel.with_mode(None, 0))
        self.assertFalse(off["brightness"]["shown"] or off["speed"]["shown"])
        none = panel.describe_lighting(None)
        self.assertFalse(none["set"])
        self.assertEqual(none["note"], "No lighting set in this profile.")


class FakePadTests(unittest.TestCase):
    def test_apply_writes_once_then_says_unchanged(self):
        pad = pads.FakePad()
        first = pad.apply(BREATHING, "dir")
        self.assertFalse(first.unchanged)
        second = pad.apply(BREATHING, "dir")
        self.assertTrue(second.unchanged)
        self.assertEqual(len(pad.writes), 1)
        self.assertEqual(len(pad.apply_calls), 2)

    def test_reading_describes_the_stock_pad(self):
        headline, now = pads.describe_reading(pads.FakePad().read())
        self.assertEqual(headline, "Pad: connected (103)")
        self.assertEqual(now, "Flow (rows) (mode 4) · brightness 4 · speed 3")

    def test_not_found(self):
        reading = pads.FakePad(connected=False).read()
        self.assertEqual(pads.describe_reading(reading), ("Pad: not found", ""))

    def test_the_no_pad_object_does_no_io(self):
        forbid_real_device(self)
        self.assertFalse(pads.NoPad().read().connected)
        with self.assertRaises(RuntimeError):
            pads.NoPad().apply(BREATHING, "dir")


class RealPadWiringTests(unittest.TestCase):
    """RealPad's calls, with `lighting.connect` swapped for a Reader-level fake: no real HID."""

    def setUp(self):
        forbid_real_device(self)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.directory = Path(tmp.name)
        self.reader = ReaderFake(self.directory)

        @contextmanager
        def connect(directory=None):
            yield self.reader, {"serial_number": "test"}

        patcher = mock.patch("glra_midi.lighting.connect", connect)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_read_only_reads(self):
        reading = pads.RealPad().read()
        self.assertTrue(reading.connected)
        self.assertEqual(reading.firmware, 103)
        self.assertEqual(reading.payload, self.reader.payload)
        self.assertEqual(self.reader.packets, [])  # nothing written
        self.assertEqual(set(self.reader.queries), {10})

    def test_a_failed_connect_reads_as_not_found(self):
        with mock.patch("glra_midi.lighting.connect", side_effect=ValueError("found 0")):
            reading = pads.RealPad().read()
        self.assertEqual(pads.describe_reading(reading)[0], "Pad: not found")
        self.assertIn("found 0", reading.detail)

    def test_apply_is_the_guarded_write(self):
        result = pads.RealPad().apply(BREATHING, self.directory)
        self.assertFalse(result.unchanged)
        self.assertEqual(len(self.reader.packets), 1)
        self.assertEqual(lights.parse(result.payload).mode, 2)
        again = pads.RealPad().apply(BREATHING, self.directory)
        self.assertTrue(again.unchanged)
        self.assertEqual(len(self.reader.packets), 1)


class DeviceCase(unittest.TestCase):
    """A Controller on the demo profile with a FakePad; the real device is off limits."""

    cooldown_ms = 0

    def setUp(self):
        forbid_real_device(self)
        self.home = make_home(self)
        self.pad = pads.FakePad()
        self.c = self.make(self.pad)

    def make(self, pad, **kw):
        c = Controller(home=self.home, pad=pad, cooldown_ms=self.cooldown_ms, **kw)
        self.addCleanup(c.deleteLater)
        c.wait_for_pad()
        return c

    @property
    def device(self):
        return self.c.device

    def lighting(self):
        return self.c.profile.lighting


class ReadTests(DeviceCase):
    def test_start_reads_the_pad_once_and_shows_it(self):
        self.assertEqual(self.pad.reads, 1)
        self.assertEqual(self.device["pad"]["headline"], "Pad: connected (103)")
        self.assertEqual(
            self.device["pad"]["text"], "Pad now: Flow (rows) (mode 4) · brightness 4 · speed 3"
        )
        self.assertEqual(
            self.device["pad"]["now"], "Flow (rows) (mode 4) · brightness 4 · speed 3"
        )
        self.assertEqual(self.c.padHeadline, "Pad: connected (103)")
        self.assertEqual(self.pad.apply_calls, [])

    def test_no_pad_object_means_not_found_and_no_io(self):
        c = Controller(home=self.home)
        self.addCleanup(c.deleteLater)
        self.assertEqual(c.padHeadline, "Pad: not found")
        self.assertFalse(c.device["apply"]["enabled"])
        c.applyLighting()  # a click with no pad does nothing
        c.setOrientation("dials-left")  # and everything else still works
        self.assertEqual(c.profile.orientation, "dials-left")

    def test_a_pad_that_is_not_found(self):
        pad = pads.FakePad(connected=False)
        c = self.make(pad)
        self.assertEqual(c.padHeadline, "Pad: not found")
        self.assertEqual(c.device["pad"]["now"], "")
        self.assertFalse(c.device["apply"]["enabled"])
        c.applyLighting()
        c.wait_for_pad()
        self.assertEqual(pad.apply_calls, [])
        # the app stays usable: edit, save
        c.setLightingMode(7)
        c.saveProfile()
        self.assertEqual(prof.load_profile(c.path).lighting.mode, 7)

    def test_refresh_reads_again(self):
        self.pad.payload = lights.build(self.pad.payload, BREATHING)
        self.c.refreshPad()
        self.c.wait_for_pad()
        self.assertEqual(self.pad.reads, 2)
        self.assertIn("Breathing", self.device["pad"]["now"])

    def test_a_pad_that_appears_after_start(self):
        pad = pads.FakePad(connected=False)
        c = self.make(pad)
        pad.connected = True
        c.refreshPad()
        c.wait_for_pad()
        self.assertTrue(c.device["pad"]["connected"])
        self.assertTrue(c.device["apply"]["enabled"])

    def test_a_read_that_raises_reads_as_not_found(self):
        pad = pads.FakePad()
        pad.read = mock.Mock(side_effect=TimeoutError("no answer"))
        c = self.make(pad)
        self.assertEqual(c.padHeadline, "Pad: not found")


class EditTests(DeviceCase):
    """Each control edits the profile, and none of them touches the pad."""

    def assert_pad_untouched(self):
        self.c.wait_for_pad()
        self.assertEqual(self.pad.apply_calls, [])
        self.assertEqual(self.pad.writes, [])

    def test_mode(self):
        self.c.setLightingMode(6)
        self.assertEqual(self.lighting().mode, 6)
        self.assertEqual(self.lighting().color, (0, 255, 255))  # Raindrop takes a colour
        self.assertTrue(self.c.dirty)
        self.assert_pad_untouched()

    def test_a_mode_without_a_colour_drops_it(self):
        self.c.setLightingMode(3)
        self.assertIsNone(self.lighting().color)
        self.assertFalse(self.device["lighting"]["color"]["shown"])
        self.assert_pad_untouched()

    def test_leave_as_it_is_removes_lighting_and_disables_apply(self):
        self.c.setLightingMode(-1)
        self.assertIsNone(self.lighting())
        self.assertFalse(self.device["lighting"]["set"])
        self.assertFalse(self.device["apply"]["enabled"])
        self.assertEqual(self.device["lighting"]["note"], "No lighting set in this profile.")
        self.c.applyLighting()
        self.assertEqual(self.device["apply"]["last"], "No lighting set in this profile.")
        self.assert_pad_untouched()

    def test_lighting_can_be_added_to_a_profile_without_it(self):
        self.c.setLightingMode(-1)
        self.c.setLightingMode(2)
        self.assertEqual(self.lighting(), Lighting(mode=2, brightness=4, speed=2))
        self.assertTrue(self.device["apply"]["enabled"])

    def test_brightness_speed(self):
        self.c.setLightingLevel("brightness", 1)
        self.c.setLightingLevel("speed", 0)
        self.assertEqual((self.lighting().brightness, self.lighting().speed), (1, 0))
        self.assert_pad_untouched()

    def test_out_of_range_level_is_refused_with_a_message(self):
        self.c.setLightingLevel("speed", 9)
        self.assertEqual(self.lighting().speed, 2)
        self.assertIn("speed must be 0..4", self.c.error)

    def test_colour_switch_and_hue(self):
        self.c.setLightingColor(False)
        self.assertIsNone(self.lighting().color)
        self.c.setLightingColor(True)
        self.assertEqual(self.lighting().color, (0, 255, 255))
        self.c.setLightingHsv(0, 120)
        self.c.setLightingHsv(1, 200)
        self.c.setLightingHsv(2, 90)
        self.assertEqual(self.lighting().color, (120, 200, 90))
        self.assertTrue(self.device["lighting"]["color"]["swatch"].startswith("#"))
        self.assert_pad_untouched()

    def test_orientation(self):
        self.c.setOrientation("dials-right")
        self.assertEqual(self.c.profile.orientation, "dials-right")
        self.assertEqual(self.device["orientation"], "dials-right")
        self.assertEqual(self.c.dialSide, "right")
        # displayed key 1 is physical key.13 in dials-right (design 6.2)
        self.assertEqual(self.c.keys[0]["control"], "key.13")
        self.assert_pad_untouched()

    def test_all_four_orientations_redraw(self):
        sides = {}
        for o in prof.ORIENTATIONS:
            self.c.setOrientation(o)
            sides[o] = self.c.dialSide
        self.assertEqual(
            sides,
            {"dials-top": "top", "dials-right": "right", "dials-bottom": "bottom", "dials-left": "left"},
        )

    def test_port_and_channel(self):
        self.c.setPort("My Pad")
        self.c.setChannel(5)
        self.assertEqual((self.c.profile.port, self.c.profile.channel), ("My Pad", 5))
        self.assertEqual(self.device["port"], {"text": "My Pad", "error": ""})
        self.assertEqual(self.device["channel"], 5)
        self.assert_pad_untouched()

    def test_an_empty_port_stays_in_the_field_with_a_message(self):
        self.c.setPort("")
        self.assertEqual(self.c.profile.port, "GLRA K16")
        self.assertEqual(self.device["port"]["text"], "")
        self.assertIn("non-empty", self.device["port"]["error"])
        self.c.setPort("Fixed")
        self.assertEqual(self.device["port"], {"text": "Fixed", "error": ""})

    def test_an_invalid_port_draft_counts_as_unsaved_and_blocks_save(self):
        # Review 10: the field showed "" while the title had no bullet and Save wrote the old port.
        self.assertFalse(self.c.dirty)
        self.c.setPort("")
        self.assertTrue(self.c.dirty)
        self.assertTrue(self.c.title.endswith("•"))
        self.assertFalse(self.c.canSave)
        self.assertFalse(self.c.canSaveAs)
        self.c.saveProfile()
        self.assertIn("Fix the MIDI port before saving", self.c.error)
        self.assertEqual(prof.load_profile(self.c.path).port, "GLRA K16")
        self.assertTrue(self.c.dirty)
        self.c.setPort("Fixed")  # a valid port ends the draft; the edit itself is unsaved
        self.assertTrue(self.c.dirty)
        self.assertTrue(self.c.canSave)
        self.c.setPort("GLRA K16")  # back to what the file holds
        self.assertFalse(self.c.dirty)

    def test_quitting_with_an_invalid_port_draft_asks(self):
        asked = []
        self.c.unsavedPrompt.connect(asked.append)
        self.c.setPort("")
        self.c.requestQuit()
        self.assertEqual(len(asked), 1)

    def test_channel_out_of_range_is_refused(self):
        self.c.setChannel(17)
        self.assertEqual(self.c.profile.channel, 1)
        self.assertIn("1..16", self.c.error)

    def test_the_edits_save_and_reload(self):
        self.c.setLightingMode(5)
        self.c.setLightingLevel("speed", 4)
        self.c.setOrientation("dials-bottom")
        self.c.setPort("Saved")
        self.c.setChannel(9)
        self.c.saveProfile()
        again = prof.load_profile(self.c.path)
        self.assertEqual(again.lighting.mode, 5)
        self.assertEqual(again.lighting.speed, 4)
        self.assertEqual(again.orientation, "dials-bottom")
        self.assertEqual((again.port, again.channel), ("Saved", 9))
        self.assert_pad_untouched()

    def test_save_open_revert_and_a_change_on_disk_never_write(self):
        self.c.setLightingMode(7)
        self.c.saveProfile()
        self.c.openProfile("default")
        self.c.revertProfile()
        self.c.setLightingMode(1)
        self.c.poll()
        self.assert_pad_untouched()


def drain_worker(controller):
    """Run the event loop until the worker is idle (the cooldown may still run)."""
    end = time.monotonic() + 2
    while not controller._worker.idle and time.monotonic() < end:
        QCoreApplication.processEvents()
        time.sleep(0.005)


class ApplyTests(DeviceCase):
    def test_apply_calls_the_pad_exactly_once_and_reports(self):
        self.c.applyLighting()
        self.c.wait_for_pad()
        self.assertEqual(len(self.pad.apply_calls), 1)
        lighting, directory = self.pad.apply_calls[0]
        self.assertEqual(lighting, BREATHING)
        self.assertEqual(Path(directory), prof.app_dir(self.home) / "backups")
        self.assertEqual(len(self.pad.writes), 1)
        apply = self.device["apply"]
        self.assertEqual((apply["last"], apply["lastKind"]), ("Applied and read back.", "ok"))
        self.assertIn("Breathing", self.device["pad"]["now"])  # the panel shows the new state
        self.assertEqual(self.pad.reads, 1)  # no second read was needed

    def test_apply_when_the_pad_already_holds_it_writes_nothing(self):
        self.pad.payload = lights.build(self.pad.payload, BREATHING)
        self.c.refreshPad()
        self.c.wait_for_pad()
        self.c.applyLighting()
        self.c.wait_for_pad()
        self.assertEqual(self.pad.writes, [])
        apply = self.device["apply"]
        self.assertEqual((apply["last"], apply["lastKind"]), ("Already set.", "info"))

    def test_a_second_click_on_unchanged_lighting_writes_nothing(self):
        self.c.applyLighting()
        self.c.wait_for_pad()
        self.c.applyLighting()
        self.c.wait_for_pad()
        self.assertEqual(len(self.pad.writes), 1)
        self.assertEqual(self.device["apply"]["last"], "Already set.")

    def test_it_applies_what_the_panel_shows_not_the_saved_file(self):
        self.c.setLightingMode(1)
        self.c.setLightingLevel("brightness", 2)
        self.c.applyLighting()
        self.c.wait_for_pad()
        self.assertEqual(self.pad.apply_calls[0][0].mode, 1)
        self.assertEqual(self.pad.apply_calls[0][0].brightness, 2)

    def test_a_readback_error_is_reported(self):
        self.pad.error = ValueError("Lighting readback did not match")
        self.c.applyLighting()
        self.c.wait_for_pad()
        apply = self.device["apply"]
        self.assertEqual(apply["lastKind"], "err")
        self.assertEqual(apply["last"], "Not applied: Lighting readback did not match")
        self.assertEqual(len(self.pad.apply_calls), 1)  # no retry
        self.assertTrue(apply["enabled"])  # the user may try again

    def test_a_write_that_read_back_differently_is_not_called_not_applied(self):
        before = self.pad.payload
        expected = lights.build(before, BREATHING)
        after = bytearray(expected)
        after[lights.HUE] = 0x80
        self.pad.error = lights.WriteNotConfirmed(
            before.hex(), expected.hex(), bytes(after).hex(), "/tmp/backups/x-lighting-before.json",
            "Lighting readback did not match.",
        )
        self.c.applyLighting()
        self.c.wait_for_pad()
        apply = self.device["apply"]
        self.assertEqual(apply["lastKind"], "warn")
        self.assertTrue(apply["last"].startswith("Written to the pad"))
        self.assertNotIn("Not applied", apply["last"])
        self.assertNotIn("paused", apply["last"])
        for text in (before.hex(), expected.hex(), bytes(after).hex(), "/tmp/backups/x-lighting-before.json"):
            self.assertIn(text, apply["last"])
        self.assertEqual(self.device["pad"]["now"], lights.describe(bytes(after)))
        self.assertTrue(apply["enabled"])  # nothing pauses later writes

    def test_nothing_sent_still_says_not_applied(self):
        self.pad.error = ValueError("Lighting changed outside the app.")
        self.c.applyLighting()
        self.c.wait_for_pad()
        self.assertEqual(self.device["apply"]["last"], "Not applied: Lighting changed outside the app.")

    def test_quit_while_a_write_runs_waits_for_it(self):
        quits = []
        self.c.quitApproved.connect(lambda: quits.append(True))
        gate = threading.Event()
        real = self.pad.apply

        def slow(lighting, directory):
            gate.wait(5)
            return real(lighting, directory)

        self.pad.apply = slow
        self.c.applyLighting()
        self.assertTrue(self.c.applying)
        self.c.requestQuit()
        self.assertEqual(quits, [])  # refused: the write is still running
        self.assertIn("pad write", self.c.notice)
        gate.set()
        self.c.wait_for_pad()
        self.assertFalse(self.c.applying)
        self.assertEqual(quits, [True])  # then it goes ahead
        self.assertEqual(self.c.notice, "")
        self.assertEqual(len(self.pad.writes), 1)

    def test_quit_waits_even_when_the_write_fails(self):
        quits = []
        self.c.quitApproved.connect(lambda: quits.append(True))
        gate = threading.Event()

        def failing(lighting, directory):
            gate.wait(5)
            raise ValueError("no")

        self.pad.apply = failing
        self.c.applyLighting()
        self.c.requestQuit()
        gate.set()
        self.c.wait_for_pad()
        self.assertEqual(quits, [True])

    def test_quit_with_no_write_running_is_immediate(self):
        quits = []
        self.c.quitApproved.connect(lambda: quits.append(True))
        self.assertFalse(self.c.applying)
        self.c.requestQuit()
        self.assertEqual(quits, [True])

    def test_shutdown_joins_the_worker(self):
        finished = []
        real = self.pad.apply

        def slow(lighting, directory):
            time.sleep(0.1)
            finished.append(True)
            return real(lighting, directory)

        self.pad.apply = slow
        self.c.applyLighting()
        self.c.shutdown()  # returns only once the worker's call has finished
        self.assertEqual(finished, [True])

    def test_a_click_while_a_write_runs_is_ignored(self):
        gate = threading.Event()
        real = self.pad.apply

        def slow(lighting, directory):
            gate.wait(5)
            return real(lighting, directory)

        self.pad.apply = slow
        self.c.applyLighting()
        self.assertTrue(self.device["apply"]["busy"])
        self.assertFalse(self.device["apply"]["enabled"])
        self.c.applyLighting()
        self.c.applyLighting()
        gate.set()
        self.c.wait_for_pad()
        self.assertEqual(len(self.pad.apply_calls), 1)

    def test_editing_during_a_write_does_not_change_what_was_sent(self):
        gate = threading.Event()
        real = self.pad.apply

        def slow(lighting, directory):
            gate.wait(5)
            return real(lighting, directory)

        self.pad.apply = slow
        self.c.applyLighting()
        self.c.setLightingMode(9)
        gate.set()
        self.c.wait_for_pad()
        self.assertEqual(self.pad.apply_calls[0][0], BREATHING)

    def test_apply_stays_off_for_a_moment_after_a_write(self):
        c = self.make(pads.FakePad(), read_on_start=True)
        c._cooldown_ms = 60
        c.applyLighting()
        # drain the worker, but not the cooldown
        drain_worker(c)
        self.assertFalse(c.device["apply"]["enabled"])
        c.wait_for_pad()
        self.assertTrue(c.device["apply"]["enabled"])

    def test_a_problem_in_the_lighting_blocks_apply(self):
        # colour on a mode that takes none cannot be reached through the panel, but a profile
        # edited some other way must not reach the pad either
        from dataclasses import replace

        self.c._edit(replace(self.c.profile, lighting=Lighting(mode=3, color=(1, 2, 3))))
        self.assertFalse(self.device["apply"]["enabled"])
        self.assertNotEqual(self.device["apply"]["problem"], "")
        self.c.applyLighting()
        self.c.wait_for_pad()
        self.assertEqual(self.pad.apply_calls, [])


class CaptureSafetyTests(unittest.TestCase):
    """`--demo` and `--capture` run on the FakePad; a capture must not reach for the device."""

    def run_capture(self, state):
        import subprocess
        import sys

        code = (
            "import sys\n"
            "from unittest import mock\n"
            "def refuse(*a, **k): raise AssertionError('the real device was reached')\n"
            "import glra_midi.lighting, glra_midi.device.backend as b\n"
            "for target in ('enumerate_devices', 'select', 'open_device'):\n"
            "    setattr(b, target, refuse)\n"
            "glra_midi.lighting.connect = refuse\n"
            "from glra_midi.app import gui\n"
            "sys.exit(gui.main(sys.argv[1:]))\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "shot.png"
            result = subprocess.run(
                [sys.executable, "-I", "-c", code, "--capture", state, "--out", str(out)],
                capture_output=True,
                text=True,
                check=False,
                env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(out.exists() and out.stat().st_size > 1000)

    def test_a_capture_that_applies_runs_on_the_fake_pad(self):
        self.run_capture("device-panel-applied")

    def test_a_capture_with_no_pad_runs_without_io(self):
        self.run_capture("device-panel-no-pad")

    def test_make_pad_picks_the_fake_for_demo_and_the_real_one_only_otherwise(self):
        from glra_midi.app import gui

        forbid_real_device(self)
        self.assertIsInstance(gui.make_pad(True), pads.FakePad)
        self.assertIsInstance(gui.make_pad(False), pads.RealPad)  # built, not opened

    def test_every_device_capture_state_is_listed(self):
        from glra_midi.app import gui

        names = [n for n in gui.STATES if n.startswith("device-")]
        self.assertGreaterEqual(len(names), 10)


class NoDeviceTests(unittest.TestCase):
    def test_a_controller_without_a_pad_never_reaches_the_device(self):
        forbid_real_device(self)
        home = make_home(self)
        c = Controller(home=home)
        self.addCleanup(c.deleteLater)
        c.refreshPad()  # even a refresh does nothing real
        c.wait_for_pad()
        c.applyLighting()
        self.assertEqual(c.padHeadline, "Pad: not found")


if __name__ == "__main__":
    unittest.main()


class HidapiThreadTests(unittest.TestCase):
    """`import hid` must happen on the thread that builds a `RealPad`, never on the pad worker
    (`fix-quit-crash`): hidapi ties its macOS IOHIDManager to the importing thread's run loop,
    and closing it from the main thread at exit crashes when that thread is gone. A stand-in
    `hid` module records which thread imported it; no real HID."""

    def setUp(self):
        forbid_real_device(self)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        (Path(tmp.name) / "hid.py").write_text(
            "import threading\nimport builtins\n"
            "builtins._hid_import_threads = getattr(builtins, '_hid_import_threads', [])\n"
            "builtins._hid_import_threads.append(threading.get_ident())\n",
            encoding="utf-8",
        )
        import builtins
        import sys

        self.builtins = builtins
        builtins._hid_import_threads = []
        saved = sys.modules.pop("hid", None)
        sys.path.insert(0, tmp.name)

        def restore():
            sys.path.remove(tmp.name)
            sys.modules.pop("hid", None)
            if saved is not None:
                sys.modules["hid"] = saved
            del builtins._hid_import_threads

        self.addCleanup(restore)

    def test_making_a_realpad_imports_hid_on_the_calling_thread(self):
        pads.RealPad()
        self.assertEqual(self.builtins._hid_import_threads, [threading.get_ident()])

    def test_a_later_import_on_the_worker_finds_it_already_loaded(self):
        pads.RealPad()
        worker = threading.Thread(target=lambda: __import__("hid"))
        worker.start()
        worker.join()
        self.assertEqual(self.builtins._hid_import_threads, [threading.get_ident()])

    def test_a_missing_hid_module_is_left_for_read_to_report(self):
        import sys

        with mock.patch.dict(sys.modules, {"hid": None}):  # makes `import hid` raise ImportError
            pads.RealPad()  # must not raise
