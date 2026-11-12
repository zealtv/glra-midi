# SPDX-License-Identifier: GPL-3.0-only

import json
import unittest
from pathlib import Path
from unittest import mock

from glra_osc import monitor
from glra_osc.decode import load_layout
from glra_osc.silence import (
    CONSUMER_PAGE,
    KEYBOARD_PAGE,
    NO_EVENT,
    Guard,
    SilenceError,
    SilenceRefused,
    Silencer,
    our_entries,
    parse_mapping,
)

FIXTURES = Path(__file__).parent / "fixtures"
CAPSLOCK = (0x700000039, 0x7000000E3)  # Bob's CapsLock -> Cmd, as observed 2026-11-12


def fixture(name):
    return (FIXTURES / name).read_text()


def render_get(services):
    """Text in hidutil's `--get` format for {registry id: [(src, dst)]}."""
    out = ["RegistryID  Key                   Value"]
    for rid, entries in services.items():
        out.append(f"{rid}   UserKeyMapping   (")
        out.append(
            ",\n".join(
                f"        {{\n        HIDKeyboardModifierMappingDst = {d};\n"
                f"        HIDKeyboardModifierMappingSrc = {s};\n    }}"
                for s, d in entries
            )
        )
        out.append(")")
    return "\n".join(line for line in out if line) + "\n"


class FakeHidutil:
    """Stands in for `hidutil`: keeps a mapping per service and speaks its text formats."""

    def __init__(self, services=None):
        self.services = {} if services is None else services
        self.calls = []
        self.fail_sets = 0  # make this many `--set` calls exit non-zero first
        self.root_only = False
        self.drop_sets = False  # accept the set but apply nothing (a failed verify)

    def run(self, *args):
        self.calls.append(args)
        if "--get" in args:
            return 0, render_get(self.services)
        payload = json.loads(args[args.index("--set") + 1])["UserKeyMapping"]
        entries = [
            (e["HIDKeyboardModifierMappingSrc"], e["HIDKeyboardModifierMappingDst"])
            for e in payload
        ]
        if self.root_only and any(src != CAPSLOCK[0] for src, _ in entries):
            return (
                1,
                "Run as root to remap alphanumerics / special characters with UserKeyMapping\n",
            )
        if self.fail_sets:
            self.fail_sets -= 1
            return 1, "boom\n"
        if not self.drop_sets:
            for rid in self.services:
                self.services[rid] = list(entries)
        return 0, ""

    def sets(self):
        return [c for c in self.calls if "--set" in c]


def make_silencer(fake, layout=None, **kwargs):
    clock = [0.0]

    def sleep(seconds):
        clock[0] += seconds

    return Silencer(layout or load_layout(), fake, sleep=sleep, clock=lambda: clock[0], **kwargs)


class ParseTests(unittest.TestCase):
    def test_original_sample_has_bobs_capslock_on_both_services(self):
        got = parse_mapping(fixture("hidutil_get_original.txt"))
        self.assertEqual(got, {"100013b79": [CAPSLOCK], "100013b85": [CAPSLOCK]})

    def test_sample_with_several_entries_keeps_order(self):
        got = parse_mapping(fixture("hidutil_get_mapped.txt"))
        self.assertEqual(list(got), ["100013c2c", "100013c34"])
        self.assertEqual(
            got["100013c2c"],
            [
                CAPSLOCK,
                (51539607786, 51539607552),  # consumer 0xEA -> 0xC00000000
                (51539607785, 30064771072),  # consumer 0xE9 -> 0x700000000
                (51539607778, 30064771327),  # consumer 0xE2 -> 0x7000000FF
            ],
        )
        self.assertEqual(got["100013c34"], got["100013c2c"])

    def test_empty_mapping_and_no_services(self):
        self.assertEqual(
            parse_mapping(fixture("hidutil_get_empty.txt")),
            {"100013c2c": [], "100013c34": []},
        )
        self.assertEqual(parse_mapping(""), {})
        self.assertEqual(parse_mapping("abc123   UserKeyMapping   (null)\n"), {"abc123": []})

    def test_garbage_is_an_error(self):
        with self.assertRaises(SilenceError):
            parse_mapping("something else entirely\n")
        with self.assertRaises(SilenceError):
            parse_mapping(
                "1a   UserKeyMapping   (\n  {\n  HIDKeyboardModifierMappingDst = 1;\n  },\n)\n"
            )


class EntriesTests(unittest.TestCase):
    def test_derived_from_the_layout_for_all_25_codes(self):
        layout = load_layout()
        entries = our_entries(layout)
        self.assertEqual(len(entries), 25)
        self.assertEqual(len({src for src, _ in entries}), 25)
        self.assertTrue(all(dst == NO_EVENT == 0x700000000 for _, dst in entries))
        self.assertIn((KEYBOARD_PAGE | 0x68, NO_EVENT), entries)  # key 1, F13
        self.assertIn((CONSUMER_PAGE | 0xE3, NO_EVENT), entries)  # dial 1 push


class ApplyRestoreTests(unittest.TestCase):
    def setUp(self):
        self.pad = {"a1": [CAPSLOCK], "a2": [CAPSLOCK]}
        self.fake = FakeHidutil(self.pad)
        self.s = make_silencer(self.fake)

    def test_apply_merges_with_bobs_entries_on_every_service(self):
        self.assertEqual(self.s.apply(), 2)
        for entries in self.pad.values():
            self.assertEqual(entries[0], CAPSLOCK)
            self.assertEqual(entries[1:], self.s.ours)

    def test_restore_sets_back_exactly_the_original(self):
        self.s.apply()
        self.s.restore()
        self.assertEqual(self.pad, {"a1": [CAPSLOCK], "a2": [CAPSLOCK]})

    def test_restore_without_apply_touches_nothing(self):
        self.s.restore()
        self.assertEqual(self.fake.calls, [])

    def test_empty_original_restores_to_empty(self):
        self.pad.update({"a1": [], "a2": []})
        self.s.apply()
        self.s.restore()
        self.assertEqual(self.pad, {"a1": [], "a2": []})

    def test_leftover_entries_from_a_killed_run_are_not_treated_as_original(self):
        self.pad.update({k: [CAPSLOCK, *self.s.ours] for k in self.pad})
        self.s.apply()
        self.assertEqual(self.pad["a1"], [CAPSLOCK, *self.s.ours])  # no duplicates
        self.s.restore()
        self.assertEqual(self.pad["a1"], [CAPSLOCK])

    def test_apply_twice_for_a_reconnect_keeps_the_same_original(self):
        self.s.apply()
        self.s.apply()
        self.s.restore()
        self.assertEqual(self.pad["a2"], [CAPSLOCK])

    def test_root_refusal_fails_at_once_without_retrying(self):
        self.fake.root_only = True
        with self.assertRaises(SilenceRefused) as ctx:
            self.s.apply()
        self.assertIn("Run as root", str(ctx.exception))
        self.assertEqual(len(self.fake.sets()), 1)
        self.assertEqual(self.pad["a1"], [CAPSLOCK])

    def test_failed_verify_is_failure_after_retrying(self):
        self.fake.drop_sets = True
        with self.assertRaisesRegex(SilenceError, "missing after the set.*gave up"):
            self.s.apply()
        self.assertGreater(len(self.fake.sets()), 1)

    def test_verify_notices_a_service_that_was_not_covered(self):
        # One service ignores the set (say it appeared a moment after hidutil ran).
        real_run = self.fake.run

        def run(*args):
            code, text = real_run(*args)
            if "--set" in args:
                self.pad["a2"] = [CAPSLOCK]
            return code, text

        self.fake.run = run
        with self.assertRaisesRegex(SilenceError, "service a2"):
            self.s.apply()

    def test_no_services_yet_retries_until_they_appear(self):
        pad = {}
        fake = FakeHidutil(pad)
        s = make_silencer(fake)
        original_get = fake.run
        gets = []

        def run(*args):
            if "--get" in args:
                gets.append(1)
                if len(gets) == 3:  # the services show up on the third look
                    pad["a1"] = [CAPSLOCK]
            return original_get(*args)

        fake.run = run
        self.assertEqual(s.apply(), 1)
        self.assertEqual(pad["a1"][0], CAPSLOCK)

    def test_no_services_ever_gives_up_with_a_reason(self):
        s = make_silencer(FakeHidutil({}))
        with self.assertRaisesRegex(SilenceError, "no services.*gave up"):
            s.apply()

    def test_a_failed_set_is_retried(self):
        self.fake.fail_sets = 2
        self.assertEqual(self.s.apply(), 2)

    def test_restore_failure_is_reported(self):
        self.s.apply()
        self.fake.fail_sets = 1
        with self.assertRaisesRegex(SilenceError, "set failed"):
            self.s.restore()


class MacosOverwriteTests(unittest.TestCase):
    """2026-11-12 replug: macOS reapplied Bob's CapsLock->Cmd, replacing the whole mapping."""

    def setUp(self):
        self.pad = {"a1": [], "a2": []}  # connect time: the CapsLock entry not applied yet
        self.fake = FakeHidutil(self.pad)
        self.s = make_silencer(self.fake)
        self.s.apply()

    def macos_overwrites(self):
        for rid in self.pad:
            self.pad[rid] = [CAPSLOCK]

    def test_next_check_reapplies_ours_and_keeps_capslock(self):
        self.macos_overwrites()
        self.assertEqual(self.s.ensure(), 25)
        for entries in self.pad.values():
            self.assertEqual(entries, [CAPSLOCK, *self.s.ours])

    def test_exit_after_that_leaves_exactly_capslock(self):
        self.macos_overwrites()
        self.s.ensure()
        self.s.restore()  # a connect-time snapshot would have put back [] here
        self.assertEqual(self.pad, {"a1": [CAPSLOCK], "a2": [CAPSLOCK]})

    def test_exit_straight_after_an_overwrite_also_leaves_capslock(self):
        self.macos_overwrites()
        self.s.restore()
        self.assertEqual(self.pad, {"a1": [CAPSLOCK], "a2": [CAPSLOCK]})

    def test_exit_with_ours_only_sets_an_empty_list(self):
        self.s.restore()
        self.assertEqual(self.pad, {"a1": [], "a2": []})
        self.assertEqual(json.loads(self.fake.sets()[-1][-1]), {"UserKeyMapping": []})

    def test_check_does_nothing_while_all_entries_are_present(self):
        before = len(self.fake.sets())
        self.assertEqual(self.s.ensure(), 0)
        self.assertEqual(len(self.fake.sets()), before)

    def test_one_service_losing_entries_is_enough(self):
        self.pad["a2"] = [CAPSLOCK, *self.s.ours[:20]]
        self.assertEqual(self.s.ensure(), 5)
        self.assertEqual(self.pad["a1"], self.pad["a2"])
        self.assertEqual(self.pad["a2"], [CAPSLOCK, *self.s.ours])

    def test_check_with_no_services_does_nothing(self):
        self.pad.clear()
        self.assertEqual(self.s.ensure(), 0)

    def test_guard_logs_one_line_and_exit_leaves_capslock(self):
        said = []
        guard = Guard(self.s, said.append)
        guard.on_pad()
        guard.tick()
        self.assertEqual(said[-1].split()[1], "pad")  # nothing new from a clean check
        count = len(said)
        self.macos_overwrites()
        guard.tick()
        self.assertEqual(said[count:], ["# pad mapping reapplied (25 entries were missing)"])
        guard.tick()
        self.assertEqual(len(said), count + 1)
        guard.close()
        self.assertEqual(self.pad, {"a1": [CAPSLOCK], "a2": [CAPSLOCK]})

    def test_guard_reports_a_failed_check_once_and_does_not_raise(self):
        said = []
        guard = Guard(self.s, said.append)
        guard.on_pad()
        self.macos_overwrites()
        self.fake.fail_sets = 2
        guard.tick()
        guard.tick()
        warnings = [line for line in said if "re-check" in line]
        self.assertEqual(len(warnings), 1)

    def test_guard_does_not_check_when_it_is_not_silencing(self):
        guard = Guard(self.s, lambda t: None)
        calls = len(self.fake.calls)
        guard.tick()
        self.assertEqual(len(self.fake.calls), calls)


class UnsilenceTests(unittest.TestCase):
    def test_works_without_saved_state_and_keeps_other_entries(self):
        other = (0x700000065, 0x700000066)
        pad = {"a1": [CAPSLOCK, other], "a2": [CAPSLOCK, other]}
        fresh = make_silencer(FakeHidutil(pad))
        pad["a1"] = pad["a2"] = [CAPSLOCK, *fresh.ours, other]
        self.assertEqual(fresh.unsilence(), 25)
        self.assertEqual(pad, {"a1": [CAPSLOCK, other], "a2": [CAPSLOCK, other]})

    def test_removes_entries_by_source_whatever_the_destination(self):
        s = make_silencer(FakeHidutil({}))
        src = s.ours[0][0]
        pad = {"a1": [CAPSLOCK, (src, 0x7000000FF)]}
        s = make_silencer(FakeHidutil(pad))
        self.assertEqual(s.unsilence(), 1)
        self.assertEqual(pad["a1"], [CAPSLOCK])

    def test_clean_or_absent_pad_sets_nothing(self):
        for pad in ({"a1": [CAPSLOCK]}, {}):
            fake = FakeHidutil(pad)
            self.assertEqual(make_silencer(fake).unsilence(), 0)
            self.assertEqual(fake.sets(), [])


class GuardTests(unittest.TestCase):
    def test_success_says_so_and_close_restores(self):
        pad = {"a1": [CAPSLOCK]}
        said = []
        guard = Guard(make_silencer(FakeHidutil(pad)), said.append)
        guard.on_pad()
        self.assertTrue(guard.active)
        self.assertIn("pad silenced", said[-1])
        guard.close()
        self.assertEqual(pad["a1"], [CAPSLOCK])
        self.assertIn("restored", said[-1])

    def test_failure_raises_without_allow_typing(self):
        fake = FakeHidutil({"a1": []})
        fake.root_only = True
        guard = Guard(make_silencer(fake), lambda t: None)
        with self.assertRaises(SilenceError):
            guard.on_pad()
        self.assertFalse(guard.active)

    def test_failure_warns_and_goes_on_with_allow_typing(self):
        fake = FakeHidutil({"a1": []})
        fake.root_only = True
        said = []
        guard = Guard(make_silencer(fake), said.append, allow_typing=True)
        guard.on_pad()
        self.assertFalse(guard.active)
        self.assertIn("WARNING", said[0])

    def test_close_reports_a_failed_restore_and_points_to_unsilence(self):
        pad = {"a1": [CAPSLOCK]}
        fake = FakeHidutil(pad)
        said = []
        guard = Guard(make_silencer(fake), said.append)
        guard.on_pad()
        fake.fail_sets = 1
        guard.close()  # does not raise
        self.assertTrue(any("unsilence" in line for line in said))


class WatchHookTests(unittest.TestCase):
    """`watch` calls on_pad when the pad appears, and again after it is lost."""

    def run_watch(self, scans, on_pad, lost_after_open=True):
        both = {"keys": {}, "consumer": {}}
        scans = list(scans)

        def find():
            return both if scans.pop(0) else {}

        def reader(source, info, events, stop):
            if lost_after_open:
                events.put(("lost", source, "unplugged"))

        with (
            mock.patch.object(monitor, "find_sources", find),
            mock.patch.object(monitor, "_reader", reader),
            mock.patch.object(monitor, "RESCAN_SECONDS", 0),
        ):
            monitor.watch(monitor.Decoder(), lambda *a: None, lambda t: None, on_pad=on_pad)

    def test_called_once_per_appearance_and_again_after_a_loss(self):
        calls = []

        def on_pad():
            calls.append(1)
            if len(calls) == 2:
                raise KeyboardInterrupt

        self.run_watch([True] * 10, on_pad)
        self.assertEqual(len(calls), 2)

    def test_not_called_while_the_pad_is_absent(self):
        calls = []

        def on_pad():
            calls.append(1)
            raise KeyboardInterrupt

        self.run_watch([False, False, True], on_pad, lost_after_open=False)
        self.assertEqual(len(calls), 1)

    def test_on_tick_runs_on_a_timer_while_the_pad_is_present(self):
        ticks = []

        def on_tick():
            ticks.append(1)
            if len(ticks) == 3:
                raise KeyboardInterrupt

        both = {"keys": {}, "consumer": {}}
        with (
            mock.patch.object(monitor, "find_sources", lambda: both),
            mock.patch.object(monitor, "_reader", lambda *a: None),
            mock.patch.object(monitor, "RESCAN_SECONDS", 0),
            mock.patch.object(monitor, "CHECK_SECONDS", 0),
        ):
            monitor.watch(
                monitor.Decoder(), lambda *a: None, lambda t: None, on_pad=lambda: None,
                on_tick=on_tick,
            )
        self.assertEqual(len(ticks), 3)

    def test_an_exception_from_the_hook_ends_the_loop(self):
        def on_pad():
            raise SilenceError("no")

        with self.assertRaises(SilenceError):
            self.run_watch([True], on_pad)


if __name__ == "__main__":
    unittest.main()
