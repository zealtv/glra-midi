# SPDX-License-Identifier: GPL-3.0-only

import io
import unittest
from unittest import mock

from glra_osc import runner
from glra_osc.mapping import MappingError

from .test_silence import FakeHidutil, make_silencer

KEY1_DOWN = bytes([0, 0, 0x68, 0, 0, 0, 0, 0])  # usage 0x68 = key 1 in the final layout
ALL_UP = bytes(8)


def run_with(script, **kwargs):
    """Run `runner.run` in dry-run mode with `watch` replaced by `script(on_report, on_lost)`."""

    def fake_watch(decoder, on_report, say, on_lost=None, on_pad=None, on_tick=None):
        script(on_report, on_lost)

    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(runner, "watch", fake_watch):
        code = runner.run(dry_run=True, out=out, err=err, **kwargs)
    return code, out.getvalue(), err.getvalue()


class RunnerTests(unittest.TestCase):
    def test_key_down_up_prints_note_on_and_off(self):
        def script(on_report, on_lost):
            on_report("keys", KEY1_DOWN, 0.0, 0.0)
            on_report("keys", ALL_UP, 0.1, 0.1)

        code, out, err = run_with(script)
        self.assertEqual(code, 0)
        self.assertIn("MIDI 90 24 7f", out)
        self.assertIn("MIDI 80 24 00", out)
        self.assertIn("no port opened", out)

    def test_no_typing_warning_by_default(self):
        _, _, err = run_with(lambda on_report, on_lost: None)
        self.assertNotIn("types", err)

    def test_allow_typing_warns_at_startup(self):
        _, _, err = run_with(lambda on_report, on_lost: None, allow_typing=True)
        self.assertIn("--allow-typing", err)
        self.assertIn("types into the focused app", err)

    def test_pad_hook_is_wired_and_restores_on_exit(self):
        pad = {"a1": [(0x700000039, 0x7000000E3)]}
        fake = FakeHidutil(pad)
        seen = []

        def fake_watch(decoder, on_report, say, on_lost=None, on_pad=None, on_tick=None):
            on_pad()
            seen.append([len(v) for v in pad.values()])

        out, err = io.StringIO(), io.StringIO()
        silencer = make_silencer(fake)
        with mock.patch.object(runner, "watch", fake_watch):
            code = runner.run(dry_run=True, out=out, err=err, silencer=silencer)
        self.assertEqual(code, 0)
        self.assertEqual(seen, [[26]])
        self.assertEqual(pad["a1"], [(0x700000039, 0x7000000E3)])
        self.assertIn("pad silenced", out.getvalue())

    def test_refuses_with_a_reason_when_silencing_fails(self):
        fake = FakeHidutil({"a1": []})
        fake.root_only = True

        def fake_watch(decoder, on_report, say, on_lost=None, on_pad=None, on_tick=None):
            on_pad()

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(runner, "watch", fake_watch):
            code = runner.run(dry_run=True, out=out, err=err, silencer=make_silencer(fake))
        self.assertEqual(code, 1)
        self.assertIn("Run as root", err.getvalue())
        self.assertIn("--allow-typing", err.getvalue())

    def test_allow_typing_carries_on_when_silencing_fails(self):
        fake = FakeHidutil({"a1": []})
        fake.root_only = True

        def fake_watch(decoder, on_report, say, on_lost=None, on_pad=None, on_tick=None):
            on_pad()
            on_report("keys", KEY1_DOWN, 0.0, 0.0)

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(runner, "watch", fake_watch):
            code = runner.run(
                dry_run=True, out=out, err=err, allow_typing=True, silencer=make_silencer(fake)
            )
        self.assertEqual(code, 0)
        self.assertIn("MIDI 90 24 7f", out.getvalue())

    def test_held_note_released_on_exit(self):
        _, out, _ = run_with(lambda on_report, on_lost: on_report("keys", KEY1_DOWN, 0.0, 0.0))
        lines = [line for line in out.splitlines() if line.startswith("MIDI")]
        self.assertEqual(len(lines), 2)
        self.assertIn("note off", lines[1])

    def test_held_note_released_on_disconnect_only_once(self):
        def script(on_report, on_lost):
            on_report("keys", KEY1_DOWN, 0.0, 0.0)
            on_lost()

        _, out, _ = run_with(script)
        self.assertEqual(out.count("note off"), 1)  # not repeated by the exit release

    def test_release_also_happens_when_the_loop_raises(self):
        def script(on_report, on_lost):
            on_report("keys", KEY1_DOWN, 0.0, 0.0)
            raise RuntimeError("boom")

        out = io.StringIO()
        with mock.patch.object(
            runner, "watch", lambda d, r, s, on_lost=None, on_pad=None, on_tick=None: script(r, on_lost)
        ):
            with self.assertRaises(RuntimeError):
                runner.run(dry_run=True, out=out, err=io.StringIO())
        self.assertIn("note off", out.getvalue())

    def test_bad_config_raises_mapping_error_before_anything_opens(self):
        with mock.patch.object(runner, "MidiPort") as port:
            with self.assertRaises(MappingError):
                runner.run(config="/nonexistent/mapping.toml", out=io.StringIO(), err=io.StringIO())
        port.assert_not_called()


if __name__ == "__main__":
    unittest.main()
