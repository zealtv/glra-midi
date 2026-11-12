# SPDX-License-Identifier: GPL-3.0-only

import io
import unittest
from unittest import mock

from glra_osc import runner
from glra_osc.mapping import MappingError

KEY1_DOWN = bytes([0, 0, 0x68, 0, 0, 0, 0, 0])  # usage 0x68 = key 1 in the final layout
ALL_UP = bytes(8)


def run_with(script, **kwargs):
    """Run `runner.run` in dry-run mode with `watch` replaced by `script(on_report, on_lost)`."""

    def fake_watch(decoder, on_report, say, on_lost=None):
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

    def test_warns_at_startup_about_missing_suppression(self):
        _, _, err = run_with(lambda on_report, on_lost: None)
        self.assertIn("silent-capture has not landed", err)
        self.assertIn("still types", err)

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
        with mock.patch.object(runner, "watch", lambda d, r, s, on_lost=None: script(r, on_lost)):
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
