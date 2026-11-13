# SPDX-License-Identifier: GPL-3.0-only

import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import time

from glra_osc import monitor, runner
from glra_osc.profile import ProfileError, profile_path, set_current

from .test_silence import FakeHidutil, make_silencer

KEY1_DOWN = bytes([0, 0, 0x68, 0, 0, 0, 0, 0])  # usage 0x68 = key 1 in the final layout
KEY2_DOWN = bytes([0, 0, 0x4A, 0, 0, 0, 0, 0])  # usage 0x4a = key 2
ALL_UP = bytes(8)

NOTE_36 = 'version = 1\n[key.1]\nkind = "note"\nnote = 36\n'
NOTE_40 = 'version = 1\n[key.1]\nkind = "note"\nnote = 40\n'
GLIDE = (
    "version = 1\n[key.1]\n"
    'kind = "cc-momentary"\ncc = 20\nlow = 0\nhigh = 100\nrise-ms = 100\nfall-ms = 50\n'
)
LAYERS = (
    "version = 1\n[layers]\ncount = 3\nnames = ['', 'Synth', '']\n"
    '[key.2]\nkind = "layer-set"\nlayer = 2\n'
    '[key.1.layers.1]\nkind = "note"\nnote = 36\n'
    '[key.1.layers.2]\nkind = "note"\nnote = 48\n'
)


def write(path, text):
    """Save as the app does: a temporary file renamed over the old one (new inode)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, path)


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class Session:
    """Runs `runner.run` in dry-run mode with `watch` replaced by `script(session)`.

    `script` gets this object: `report` feeds a pad report at time `t`, `wake(t)` calls the
    loop's `on_wake` as `watch` would, `wake_at()` asks when it wants waking, `lost()` is a
    disconnect and `lines` is what has been printed so far."""

    def __init__(self, tmp):
        self.home = Path(tmp)
        self.out, self.err = io.StringIO(), io.StringIO()
        self.clock = FakeClock()
        self.hooks = {}

    def fake_watch(self, decoder, on_report, say, **hooks):
        self.hooks = dict(hooks, on_report=on_report)
        self.script(self)

    def report(self, source, data, t):
        self.clock.now = t
        self.hooks["on_report"](source, data, t, 1_700_000_000.0 + t)

    def wake(self, t):
        self.clock.now = t
        self.hooks["on_wake"](t)

    def wake_at(self):
        return self.hooks["wake_at"]()

    def lost(self):
        self.hooks["on_lost"]()

    @property
    def lines(self):
        return self.out.getvalue().splitlines()

    @property
    def midi(self):
        return [line[5:] for line in self.lines if line.startswith("MIDI ")]

    def run(self, script, **kwargs):
        self.script = script
        kwargs.setdefault("home", self.home)
        with mock.patch.object(runner, "watch", self.fake_watch):
            return runner.run(
                dry_run=True, out=self.out, err=self.err, clock=self.clock, **kwargs
            )


class TempHome(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.session = Session(self.tmp / "home")

    def profile(self, text, name="default"):
        path = profile_path(name, self.session.home)
        write(path, text)
        return path


class PlayTests(TempHome):
    def test_default_profile_is_created_and_played_without_config(self):
        def script(s):
            s.report("keys", KEY1_DOWN, 0.0)
            s.report("keys", ALL_UP, 0.1)

        self.assertEqual(self.session.run(script), 0)
        self.assertTrue(profile_path("default", self.session.home).is_file())
        # the shipped default: layer 1, key 1 is note 36 on channel 1
        self.assertEqual([m.split("  ")[0] for m in self.session.midi], ["90 24 7f", "80 24 00"])
        self.assertIn("no port opened", self.session.out.getvalue())
        self.assertIn("default.toml", self.session.out.getvalue())

    def test_config_plays_that_file_and_ignores_the_pointer(self):
        self.profile(NOTE_36, "default")
        path = self.tmp / "mine.toml"
        write(path, NOTE_40)
        self.session.run(lambda s: s.report("keys", KEY1_DOWN, 0.0), config=str(path))
        self.assertIn("90 28 7f", self.session.midi[0])

    def test_the_current_pointer_picks_the_profile(self):
        self.profile(NOTE_36, "default")
        self.profile(NOTE_40, "drums")
        set_current("drums", self.session.home)
        self.session.run(lambda s: s.report("keys", KEY1_DOWN, 0.0))
        self.assertIn("90 28 7f", self.session.midi[0])

    def test_an_old_mapping_file_is_refused_before_anything_opens(self):
        path = self.tmp / "old.toml"
        write(path, "[midi]\nchannel = 1\n")
        with mock.patch.object(runner, "MidiPort") as port:
            with self.assertRaises(ProfileError) as ctx:
                runner.run(config=str(path), out=io.StringIO(), err=io.StringIO())
        self.assertIn("version", str(ctx.exception))
        port.assert_not_called()

    def test_a_missing_config_raises_profile_error(self):
        with mock.patch.object(runner, "MidiPort") as port:
            with self.assertRaises(ProfileError):
                runner.run(config="/nonexistent/p.toml", out=io.StringIO(), err=io.StringIO())
        port.assert_not_called()

    def test_no_typing_warning_by_default(self):
        self.session.run(lambda s: None)
        self.assertNotIn("types", self.session.err.getvalue())

    def test_allow_typing_warns_at_startup(self):
        self.session.run(lambda s: None, allow_typing=True)
        self.assertIn("--allow-typing", self.session.err.getvalue())
        self.assertIn("types into the focused app", self.session.err.getvalue())

    def test_pad_hook_is_wired_and_restores_on_exit(self):
        pad = {"a1": [(0x700000039, 0x7000000E3)]}
        fake = FakeHidutil(pad)
        seen = []

        def script(s):
            s.hooks["on_pad"]()
            seen.append([len(v) for v in pad.values()])

        code = self.session.run(script, silencer=make_silencer(fake))
        self.assertEqual(code, 0)
        self.assertEqual(seen, [[26]])
        self.assertEqual(pad["a1"], [(0x700000039, 0x7000000E3)])
        self.assertIn("pad silenced", self.session.out.getvalue())

    def test_refuses_with_a_reason_when_silencing_fails(self):
        fake = FakeHidutil({"a1": []})
        fake.root_only = True
        code = self.session.run(lambda s: s.hooks["on_pad"](), silencer=make_silencer(fake))
        self.assertEqual(code, 1)
        self.assertIn("Run as root", self.session.err.getvalue())
        self.assertIn("--allow-typing", self.session.err.getvalue())

    def test_allow_typing_carries_on_when_silencing_fails(self):
        fake = FakeHidutil({"a1": []})
        fake.root_only = True

        def script(s):
            s.hooks["on_pad"]()
            s.report("keys", KEY1_DOWN, 0.0)

        code = self.session.run(script, allow_typing=True, silencer=make_silencer(fake))
        self.assertEqual(code, 0)
        self.assertIn("90 24 7f", self.session.out.getvalue())


class ReleaseTests(TempHome):
    def test_held_note_released_on_exit(self):
        self.session.run(lambda s: s.report("keys", KEY1_DOWN, 0.0))
        self.assertEqual(len(self.session.midi), 2)
        self.assertIn("note off", self.session.midi[1])

    def test_held_note_released_on_disconnect_only_once(self):
        def script(s):
            s.report("keys", KEY1_DOWN, 0.0)
            s.lost()

        self.session.run(script)
        self.assertEqual(self.session.out.getvalue().count("note off"), 1)

    def test_release_also_happens_when_the_loop_raises(self):
        def script(s):
            s.report("keys", KEY1_DOWN, 0.0)
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            self.session.run(script)
        self.assertIn("note off", self.session.out.getvalue())


class GlideTests(TempHome):
    def test_run_ticks_the_engine_and_a_glide_comes_out_in_order(self):
        self.profile(GLIDE)

        def script(s):
            s.report("keys", KEY1_DOWN, 0.0)
            # idle until the glide starts: the next wake is only the reload poll
            self.assertEqual(s.wake_at(), 0.01)
            for step in range(1, 11):
                s.wake(step * 0.01)
            self.assertEqual(s.wake_at(), runner.RELOAD_POLL_SECONDS)  # glide over: idle again

        self.session.run(script)
        values = [int(m.split()[2], 16) for m in self.session.midi if m.startswith("b0 14")]
        self.assertEqual(values[:10], list(range(10, 101, 10)))
        self.assertEqual(values[10:], [0])  # key 1 still held: the exit release

    def test_wake_before_the_tick_is_due_sends_nothing(self):
        self.profile(GLIDE)

        def script(s):
            s.report("keys", KEY1_DOWN, 0.0)
            s.wake(0.004)

        self.session.run(script)
        values = [int(m.split()[2], 16) for m in self.session.midi if m.startswith("b0 14")]
        self.assertEqual(values, [0])  # only the release on exit; no glide value before 10 ms

    def test_release_while_gliding_glides_back_to_low(self):
        self.profile(GLIDE)

        def script(s):
            s.report("keys", KEY1_DOWN, 0.0)
            for step in range(1, 6):
                s.wake(step * 0.01)
            s.report("keys", ALL_UP, 0.05)  # fall-ms = 50, from 50
            for step in range(6, 11):
                s.wake(step * 0.01)

        self.session.run(script)
        values = [int(m.split()[2], 16) for m in self.session.midi if m.startswith("b0 14")]
        self.assertEqual(values[:5], [10, 20, 30, 40, 50])
        self.assertEqual(values[-1], 0)
        self.assertEqual(values, sorted(values[:5]) + sorted(values[5:], reverse=True))


class ReloadTests(TempHome):
    def setUp(self):
        super().setUp()
        self.path = self.profile(NOTE_36)

    def test_a_changed_file_swaps_the_engine_and_releases_held_notes(self):
        def script(s):
            s.report("keys", KEY1_DOWN, 0.0)  # note 36 on
            write(self.path, NOTE_40)
            s.wake(0.2)  # before the poll: nothing yet
            self.assertNotIn("reloaded", s.out.getvalue())
            s.wake(0.6)
            s.report("keys", ALL_UP, 0.7)  # belongs to the old engine: nothing more to send
            s.report("keys", KEY1_DOWN, 0.8)  # note 40 on

        self.session.run(script)
        shown = [m.split("  ")[0] for m in self.session.midi]
        self.assertEqual(shown[:3], ["90 24 7f", "80 24 00", "90 28 7f"])
        self.assertEqual(self.session.out.getvalue().count("# reloaded"), 1)

    def test_a_held_glide_goes_to_low_on_reload(self):
        write(self.path, GLIDE.replace("rise-ms = 100", "rise-ms = 1000"))

        def script(s):
            s.report("keys", KEY1_DOWN, 0.0)
            for step in range(1, 4):
                s.wake(step * 0.01)  # 30
            write(self.path, NOTE_40)
            s.wake(0.6)

        self.session.run(script)
        values = [int(m.split()[2], 16) for m in self.session.midi if m.startswith("b0 14")]
        self.assertEqual(values[:3], [1, 2, 3])
        self.assertEqual(values[-1], 0)  # the reload's release; not left mid-glide
        self.assertNotIn(100, values)

    def test_a_latched_cc_and_the_cc_table_survive_a_reload(self):
        latch = GLIDE.replace("rise-ms = 100", 'mode = "latch"\nrise-ms = 0')
        write(self.path, latch)

        def script(s):
            s.report("keys", KEY1_DOWN, 0.0)  # latches at 100
            s.report("keys", ALL_UP, 0.1)
            write(self.path, latch + "# edited\n")
            s.wake(0.6)  # reload
            s.report("keys", KEY1_DOWN, 0.7)  # still latched: this press unlatches

        self.session.run(script)
        values = [int(m.split()[2], 16) for m in self.session.midi if m.startswith("b0 14")]
        self.assertEqual(values, [100, 0])

    def test_an_invalid_file_keeps_the_old_profile_and_reports_once(self):
        def script(s):
            write(self.path, "version = 1\n[key.1]\nkind = 'nope'\n")
            s.wake(0.6)
            s.wake(1.2)
            s.wake(1.8)
            s.report("keys", KEY1_DOWN, 1.9)  # still note 36
            write(self.path, NOTE_40)
            s.wake(2.4)
            s.report("keys", ALL_UP, 2.5)
            s.report("keys", KEY1_DOWN, 2.6)

        self.session.run(script)
        out = self.session.out.getvalue()
        self.assertEqual(out.count("not reloaded"), 1)
        self.assertIn("kind", out)
        shown = [m.split("  ")[0] for m in self.session.midi]
        self.assertEqual(shown[:3], ["90 24 7f", "80 24 00", "90 28 7f"])
        self.assertEqual(out.count("# reloaded"), 1)

    def test_a_file_that_goes_missing_keeps_the_old_profile(self):
        def script(s):
            self.path.unlink()
            s.wake(0.6)  # `current` falls back to default.toml, recreated from the shipped one
            s.report("keys", KEY1_DOWN, 0.7)

        self.session.run(script)
        self.assertIn("90 24 7f", self.session.out.getvalue())  # shipped default: note 36 too

    def test_the_active_layer_survives_a_reload_when_it_still_exists(self):
        write(self.path, LAYERS)

        def script(s):
            s.report("keys", KEY2_DOWN, 0.0)  # layer-set 2
            s.report("keys", ALL_UP, 0.1)
            write(self.path, LAYERS + "# edited\n")
            s.wake(0.6)
            s.report("keys", KEY1_DOWN, 0.7)  # layer 2's note 48

        self.session.run(script)
        self.assertIn("# layer 1 -> 2 'Synth'", self.session.out.getvalue())
        self.assertIn("90 30 7f", self.session.out.getvalue())

    def test_the_layer_falls_back_to_1_when_it_no_longer_exists(self):
        write(self.path, LAYERS)

        def script(s):
            s.report("keys", KEY2_DOWN, 0.0)
            s.report("keys", ALL_UP, 0.1)
            write(self.path, 'version = 1\n[layers]\ncount = 1\n[key.1]\nkind = "note"\nnote = 40\n')
            s.wake(0.6)
            s.report("keys", KEY1_DOWN, 0.7)

        self.session.run(script)
        self.assertIn("90 28 7f", self.session.out.getvalue())

    def test_switching_the_current_pointer_reloads(self):
        self.profile(NOTE_40, "drums")

        def script(s):
            set_current("drums", self.session.home)
            s.wake(0.6)
            s.report("keys", KEY1_DOWN, 0.7)

        self.session.run(script)
        self.assertIn("90 28 7f", self.session.out.getvalue())
        self.assertIn("drums.toml", self.session.out.getvalue())

    def test_with_config_the_pointer_is_not_followed(self):
        other = self.tmp / "other.toml"
        write(other, NOTE_36)
        self.profile(NOTE_40, "drums")

        def script(s):
            set_current("drums", self.session.home)
            s.wake(0.6)
            s.report("keys", KEY1_DOWN, 0.7)

        self.session.run(script, config=str(other))
        self.assertIn("90 24 7f", self.session.out.getvalue())
        self.assertNotIn("# reloaded", self.session.out.getvalue())

    def test_a_changed_port_name_is_noted_not_applied(self):
        def script(s):
            write(self.path, 'version = 1\n[midi]\nport = "Other"\n')
            s.wake(0.6)

        self.session.run(script)
        self.assertIn("restart `run` to use 'Other'", self.session.out.getvalue())


class DryRunLabelTests(TempHome):
    def test_dry_run_labels_events_with_the_profile_orientation(self):
        self.profile('version = 1\n[pad]\norientation = "dials-right"\n[key.1]\nkind = "note"\nnote = 36\n')
        self.session.run(lambda s: s.report("keys", KEY1_DOWN, 0.0))
        events = [line for line in self.session.lines if "KEY" in line]
        self.assertEqual(len(events), 1)
        self.assertIn("[key.1]", events[0])
        self.assertNotIn("KEY 01 [key.1]", events[0])  # dials-right renumbers key 1

    def test_a_reload_changes_the_labels(self):
        self.profile(NOTE_36)

        def script(s):
            s.report("keys", KEY1_DOWN, 0.0)
            s.report("keys", ALL_UP, 0.1)
            write(
                profile_path("default", self.session.home),
                'version = 1\n[pad]\norientation = "dials-right"\n[key.1]\nkind = "note"\nnote = 36\n',
            )
            s.wake(0.6)
            s.report("keys", KEY1_DOWN, 0.7)

        self.session.run(script)
        events = [line for line in self.session.lines if "KEY" in line and "DOWN" in line]
        self.assertIn("KEY 01 [key.1]", events[0])
        self.assertNotIn("KEY 01 [key.1]", events[1])


class WatchWakeTests(unittest.TestCase):
    """`watch` sleeps no longer than `wake_at` says and calls `on_wake` after queued reports."""

    def watch(self, reader, **hooks):
        with (
            mock.patch.object(monitor, "find_sources", lambda: {"keys": {}, "consumer": {}}),
            mock.patch.object(monitor, "_reader", reader),
        ):
            monitor.watch(monitor.Decoder(), hooks.pop("on_report"), lambda t: None, **hooks)

    def test_on_wake_runs_on_schedule_not_on_the_slow_default_wait(self):
        woken = []

        def on_wake(now):
            woken.append(now)
            if len(woken) == 5:
                raise KeyboardInterrupt

        started = time.monotonic()
        self.watch(
            lambda *a: None,
            on_report=lambda *a: None,
            on_wake=on_wake,
            wake_at=lambda: time.monotonic() + 0.02,
        )
        self.assertLess(time.monotonic() - started, 0.5)  # five 0.25 s default waits would be 1.25 s
        self.assertEqual(len(woken), 5)

    def test_a_queued_report_is_handled_before_the_wake_that_follows(self):
        order = []

        def reader(source, info, events, stop):
            if source == "keys":
                events.put(("report", source, KEY1_DOWN, time.monotonic(), time.time()))

        def on_wake(now):
            order.append("wake")
            raise KeyboardInterrupt

        self.watch(
            reader,
            on_report=lambda *a: order.append("report"),
            on_wake=on_wake,
            wake_at=lambda: None,
        )
        self.assertEqual(order[:2], ["report", "wake"])


if __name__ == "__main__":
    unittest.main()
