# SPDX-License-Identifier: GPL-3.0-only

"""Lighting modes: payloads, the guarded write and `glra-midi lights`, all on a fake pad."""

import io
import json
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from glra_midi import lighting, profile
from glra_midi.device import lighting as studio
from glra_midi.device import transactions
from glra_midi.device.model import demo_table
from glra_midi.device.storage import load
from glra_midi.lighting import LightingError, build, check, describe, parse
from glra_midi.profile import Lighting

# What `glean:k16n3-lighting` records on Bob's pad: stock mode 4, direction 3, byte 7 = 8.
STOCK = bytes.fromhex("0100040403030008ffffff")
ALLOWED = {2, 3, 4, 6, 8, 9, 10}  # the bytes `apply` may change (design section 5.3)
# The two readback mismatches from Bob's tour (2026-11-13): firmware 103 normalised bytes.
CAPTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "lighting_readback_captures.json").read_text()
)["captures"]
FLOW = Lighting(mode=5, brightness=4, speed=4)
BREATHING_COLOUR = Lighting(mode=2, brightness=4, speed=4, color=(215, 255, 255))
CAPTURE_WANTED = {"flow-columns-colour-off": FLOW, "breathing-colour-on-h215": BREATHING_COLOUR}


class Audit:
    def record(self, *args, **kwargs):
        pass


class FakePad:
    """Stands in for `Reader` and its device: answers the reads, takes one lighting write."""

    def __init__(self, directory, payload=STOCK, firmware=103, internal_pid=0x2475):
        self.audit = Audit()
        self.device = self
        self.directory = Path(directory)
        self.payload = bytearray(payload)
        self.firmware, self.internal_pid = firmware, internal_pid
        self.tables = {p: bytearray(demo_table()) for p in range(6)}
        self.rgb = bytes(range(256)) + bytes(176)
        self.packets = []  # every packet written, as sent
        self.queries = []  # every read opcode asked
        self.stored = None  # what a write leaves in the pad, if not the payload sent
        self.ack_echoes_stored = False  # the ack carries what the pad kept, not what was sent
        self.ack = b""

    def status(self):
        return dict(
            version=1,
            internal_pid=self.internal_pid,
            firmware=self.firmware,
            profile_count=6,
            layer_count=1,
            current_profile=0,
            current_layer=0,
        )

    def query(self, command, offset=0, length=0, profile=0):
        self.queries.append(command)
        assert command == 10, f"only the lighting read is expected, got {command}"
        return bytes([0xAA, 0x0A, 11, 0, 0]) + bytes(self.payload) + bytes(48)

    def memory(self, command, size, profile=0):
        self.queries.append(command)
        if command == 19:
            return self.rgb[:size]
        return bytes(self.tables[profile][:size])

    def write(self, data):
        assert list(self.directory.glob("*-lighting-before.json")), "a backup must come first"
        self.packets.append(bytes(data))
        sent = bytes(data[6:17])
        self.payload = bytearray(self.stored if self.stored is not None else sent)
        echoed = bytes(self.payload) if self.ack_echoes_stored else sent
        self.ack = bytes([0xAA, 0x0B, 1, 0, 0]) + echoed + bytes(48)
        return len(data)

    def read(self, size, timeout):
        return self.ack


class PayloadTests(unittest.TestCase):
    def test_table_agrees_with_profile_py(self):
        self.assertEqual([m.number for m in lighting.MODES], list(profile.LIGHTING_MODES))
        self.assertEqual(
            {m.number for m in lighting.MODES if m.color}, set(profile.LIGHTING_COLOR_MODES)
        )

    def test_table_names_the_thirteen_modes(self):
        names = {m.number: m.name for m in lighting.MODES}
        self.assertEqual(len(names), 13)
        self.assertEqual(names[0], "Off")
        self.assertEqual(names[3], "Spectrum")
        self.assertEqual(names[12], "Custom")

    def test_every_mode_builds_and_parses(self):
        for m in lighting.MODES:
            with self.subTest(mode=m.number):
                new = build(STOCK, Lighting(mode=m.number, brightness=3, speed=1))
                state = parse(new)
                self.assertEqual(state.mode, m.number)
                self.assertEqual(state.brightness, 3 if m.brightness else STOCK[3])
                self.assertEqual(state.speed, 1 if m.speed else STOCK[4])
                self.assertEqual(state.color_flag, 0)

    def test_only_the_allowed_bytes_change(self):
        for m in lighting.MODES:
            colours = [None, (10, 20, 30)] if m.color else [None]
            for color in colours:
                with self.subTest(mode=m.number, color=color):
                    new = build(STOCK, Lighting(mode=m.number, brightness=0, speed=0, color=color))
                    changed = {i for i in range(11) if new[i] != STOCK[i]}
                    self.assertLessEqual(changed, ALLOWED)
                    self.assertEqual(new[0:2], b"\x01\x00")
                    self.assertEqual((new[5], new[7]), (STOCK[5], STOCK[7]))  # direction, byte 7

    def test_direction_and_byte7_survive_odd_values(self):
        odd = bytes.fromhex("0100020201aa0077112233")
        new = build(odd, Lighting(mode=6, brightness=4, speed=4, color=(1, 2, 3)))
        self.assertEqual(new.hex(), "0100060404aa0177010203")

    def test_colour_sets_flag_and_hsv(self):
        new = build(STOCK, Lighting(mode=2, brightness=4, speed=2, color=(0, 255, 255)))
        self.assertEqual(new.hex(), "0100020402030108" + "00ffff")
        state = parse(new)
        self.assertEqual(state.color, (0, 255, 255))

    def test_no_colour_clears_flag_and_keeps_hsv(self):
        held = bytes.fromhex("0100020402030108" + "55ff80")
        new = build(held, Lighting(mode=2, brightness=4, speed=2))
        self.assertEqual(new[6], 0)
        self.assertEqual(new[8:11], bytes.fromhex("55ff80"))
        self.assertIsNone(parse(new).color)

    def test_out_of_range_values_are_refused(self):
        bad = [
            Lighting(mode=13),
            Lighting(mode=-1),
            Lighting(mode=2, brightness=5),
            Lighting(mode=2, brightness=-1),
            Lighting(mode=2, speed=5),
            Lighting(mode=2, speed=True),
            Lighting(mode=2, color=(256, 0, 0)),
            Lighting(mode=2, color=(0, 0, -1)),
            Lighting(mode=2, color=(0, 0)),
            Lighting(mode=3, color=(0, 255, 255)),  # Spectrum takes no single colour
            Lighting(mode=0, color=(0, 255, 255)),
            Lighting(mode=12, color=(0, 255, 255)),
        ]
        for value in bad:
            with self.subTest(value=value):
                with self.assertRaises(LightingError):
                    check(value)
                with self.assertRaises(LightingError):
                    build(STOCK, value)

    def test_bad_payloads_are_refused(self):
        for raw in (STOCK[:10], STOCK + b"\0", b"\x02" + STOCK[1:], b"\x01\x01" + STOCK[2:]):
            with self.subTest(raw=raw.hex()):
                with self.assertRaises(LightingError):
                    parse(raw)
        with self.assertRaises(LightingError):
            parse(STOCK[:2] + bytes([13]) + STOCK[3:])

    def test_describe_and_changes(self):
        self.assertEqual(describe(STOCK), "Flow (rows) (mode 4) · brightness 4 · speed 3")
        new = build(STOCK, Lighting(mode=2, brightness=4, speed=2, color=(0, 255, 255)))
        self.assertIn("one colour h0 s255 v255", describe(new))
        self.assertEqual(
            lighting.changes(STOCK, new),
            [
                ("mode", 4, 2),
                ("speed", 3, 2),
                ("color_flag", 0, 1),
                ("hsv", (255, 255, 255), (0, 255, 255)),
            ],
        )
        self.assertEqual(lighting.changes(STOCK, STOCK), [])

    def test_lighting_is_never_imported_by_load_run_or_profile(self):
        for name in ("profile.py", "runner.py", "engine.py", "monitor.py"):
            source = (Path(lighting.__file__).parent / name).read_text()
            with self.subTest(module=name):
                self.assertNotIn("from .lighting", source)
                self.assertNotIn("import lighting", source)


class ReadbackTests(unittest.TestCase):
    """Firmware 103 normalises bytes; `readback_differences` ignores exactly those."""

    def test_the_captures_are_what_build_makes_and_differ_as_recorded(self):
        for c in CAPTURES:
            with self.subTest(capture=c["name"]):
                before = bytes.fromhex(c["before"])
                expected = bytes.fromhex(c["expected"])
                self.assertEqual(build(before, CAPTURE_WANTED[c["name"]]), expected)
                self.assertNotEqual(expected, bytes.fromhex(c["after"]))  # the old check failed

    def test_both_captures_count_as_read_back(self):
        for c in CAPTURES:
            with self.subTest(capture=c["name"]):
                found = lighting.readback_differences(
                    bytes.fromhex(c["expected"]), bytes.fromhex(c["after"])
                )
                self.assertEqual(found, [])

    def test_identical_payloads_have_no_differences(self):
        self.assertEqual(lighting.readback_differences(STOCK, STOCK), [])

    def test_byte7_never_counts_and_hsv_counts_only_with_the_flag_on(self):
        off = bytes.fromhex("0100020404030008aaffff")
        self.assertEqual(lighting.readback_differences(off, bytes.fromhex("01000204040300ff112233")), [])
        on = bytes.fromhex("0100020404030108d7ffff")
        self.assertEqual(
            lighting.readback_differences(on, bytes.fromhex("01000204040301ffd8ffff")),
            [("hsv", (215, 255, 255), (216, 255, 255))],
        )

    def test_every_other_difference_is_still_reported(self):
        sent = bytes.fromhex("0100020403030108d7ffff")
        cases = {
            "mode": ("0100030403030108d7ffff", [("mode", 2, 3)]),
            "brightness": ("0100020303030108d7ffff", [("brightness", 4, 3)]),
            "speed": ("0100020402030108d7ffff", [("speed", 3, 2)]),
            "direction": ("0100020403020108d7ffff", [("direction", 3, 2)]),
            "colour flag": ("0100020403030008d7ffff", [("color_flag", 1, 0)]),
        }
        for what, (after, expected) in cases.items():
            with self.subTest(what=what):
                self.assertEqual(lighting.readback_differences(sent, bytes.fromhex(after)), expected)

    def test_brightness_and_speed_count_only_where_the_mode_reads_them(self):
        # Steady (1) reads brightness, not speed; Custom (12) reads brightness, not speed.
        sent = bytes.fromhex("0100010402030008ffffff")
        self.assertEqual(lighting.readback_differences(sent, bytes.fromhex("0100010400030008ffffff")), [])
        self.assertEqual(
            lighting.readback_differences(sent, bytes.fromhex("0100010102030008ffffff")),
            [("brightness", 4, 1)],
        )

    def test_a_bad_readback_payload_is_refused_not_ignored(self):
        with self.assertRaises(LightingError):
            lighting.readback_differences(STOCK, STOCK[:10])


class ReadTests(unittest.TestCase):
    def test_read_payload_uses_only_the_lighting_read(self):
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder)
            self.assertEqual(lighting.read_payload(pad), STOCK)
            self.assertEqual(pad.queries, [10])
            self.assertEqual(pad.packets, [])

    def test_read_refuses_a_short_or_unknown_reply(self):
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder)
            pad.query = lambda command, *a: bytes([0xAA, 0x0A, 7, 0, 0]) + bytes(59)
            with self.assertRaises(LightingError):
                lighting.read_payload(pad)
            pad.query = (
                lambda command, *a: bytes([0xAA, 0x0A, 11, 0, 0]) + bytes([1, 0, 99]) + bytes(56)
            )
            with self.assertRaises(LightingError):
                lighting.read_payload(pad)


class ApplyTests(unittest.TestCase):
    def apply(self, pad, value, folder):
        return lighting.apply(pad, {"serial_number": "test"}, value, Path(folder) / "backups")

    def test_every_mode_writes_once_with_backup_and_readback(self):
        for m in lighting.MODES:
            with self.subTest(mode=m.number), tempfile.TemporaryDirectory() as folder:
                pad = FakePad(folder)
                pad.directory = Path(folder) / "backups"
                wanted = Lighting(mode=m.number, brightness=2, speed=1)
                result = self.apply(pad, wanted, folder)
                self.assertTrue(result["verified"])
                self.assertEqual(len(pad.packets), 1)
                self.assertEqual(bytes(pad.payload), build(STOCK, wanted))
                self.assertEqual(load(result["backup"])["before"], STOCK.hex())

    def test_the_packet_is_one_06_0b_write_of_eleven_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder)
            pad.directory = Path(folder) / "backups"
            self.apply(pad, Lighting(mode=2, brightness=4, speed=2, color=(0, 255, 255)), folder)
            (packet,) = pad.packets
            self.assertEqual(len(packet), 65)
            self.assertEqual(packet[:6], bytes([0, 6, 0x0B, 0x0B, 0, 0]))
            self.assertEqual(packet[17:], bytes(48))  # nothing past the 11 bytes
            self.assertNotIn(0x14, packet[1:4])  # not 06 14
            self.assertNotIn(0x12, packet[1:3])  # not 06 12

    def test_no_write_when_the_pad_already_holds_it(self):
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder)
            pad.directory = Path(folder) / "backups"
            same = Lighting(mode=4, brightness=4, speed=3)  # STOCK, keeping HSV as read
            result = self.apply(pad, same, folder)
            self.assertTrue(result["unchanged"])
            self.assertEqual(pad.packets, [])
            self.assertEqual(list(Path(folder).rglob("*.json")), [])  # not even a backup
            self.assertEqual(pad.queries, [10])  # one lighting read, nothing else

    def test_firmware_103_normalising_reads_back_as_applied(self):
        for c in CAPTURES:
            with self.subTest(capture=c["name"]), tempfile.TemporaryDirectory() as folder:
                pad = FakePad(folder, payload=bytes.fromhex(c["before"]))
                pad.directory = Path(folder) / "backups"
                pad.stored = bytes.fromhex(c["after"])
                result = self.apply(pad, CAPTURE_WANTED[c["name"]], folder)
                self.assertTrue(result["verified"])
                self.assertEqual(len(pad.packets), 1)
                self.assertEqual(pad.packets[0][6:17].hex(), c["expected"])
                # what the pad holds is reported, not what was sent
                self.assertEqual(result["after"], c["after"])
                self.assertEqual(bytes(pad.payload).hex(), c["after"])
                changed = {n["byte"] for n in result["normalised"]}
                self.assertTrue(changed and changed <= {7, 8})
                record = Path(result["backup"].replace("-lighting-before", "-lighting-normalised"))
                self.assertEqual(load(record)["held"], c["after"])
                self.assertEqual(load(record)["sent"], c["expected"])

    def test_a_pad_that_keeps_what_was_sent_has_nothing_normalised(self):
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder)
            pad.directory = Path(folder) / "backups"
            result = self.apply(pad, Lighting(mode=3, brightness=2, speed=2), folder)
            self.assertNotIn("normalised", result)
            self.assertEqual(result["after"], bytes(pad.payload).hex())

    def test_an_ack_that_echoes_the_normalised_bytes_still_confirms(self):
        c = CAPTURES[1]
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder, payload=bytes.fromhex(c["before"]))
            pad.directory = Path(folder) / "backups"
            pad.stored, pad.ack_echoes_stored = bytes.fromhex(c["after"]), True
            result = self.apply(pad, BREATHING_COLOUR, folder)
            self.assertTrue(result["verified"])
            self.assertEqual(result["after"], c["after"])

    def test_a_real_difference_next_to_a_normalised_one_still_fails(self):
        c = CAPTURES[1]  # normalised byte 7, plus the pad kept speed 2 instead of 4
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder, payload=bytes.fromhex(c["before"]))
            pad.directory = Path(folder) / "backups"
            pad.stored = bytes.fromhex("01000204020301ffd7ffff")
            with self.assertRaises(lighting.WriteNotConfirmed) as ctx:
                self.apply(pad, BREATHING_COLOUR, folder)
            self.assertEqual(ctx.exception.after, "01000204020301ffd7ffff")
            self.assertEqual(len(pad.packets), 1)

    def test_the_vendored_read_is_restored_after_every_write(self):
        original = studio.read
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder, payload=bytes.fromhex(CAPTURES[0]["before"]))
            pad.directory = Path(folder) / "backups"
            pad.stored = bytes.fromhex(CAPTURES[0]["after"])
            self.apply(pad, FLOW, folder)
            self.assertIs(studio.read, original)
            pad.stored = bytes.fromhex("0100010101010008ffffff")
            with self.assertRaises(lighting.WriteNotConfirmed):
                self.apply(pad, Lighting(mode=3, brightness=2, speed=2), folder)
            self.assertIs(studio.read, original)

    def test_readback_mismatch_is_reported_and_leaves_an_error_record(self):
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder)
            pad.directory = Path(folder) / "backups"
            pad.stored = bytes.fromhex("0100010101010008ffffff")  # the pad kept something else
            with self.assertRaises(lighting.WriteNotConfirmed) as ctx:
                self.apply(pad, Lighting(mode=3, brightness=2, speed=2), folder)
            self.assertEqual(len(pad.packets), 1)  # one write, no retry
            self.assertTrue(list((Path(folder) / "backups").glob("*-lighting-error.json")))
            err = ctx.exception
            # before / expected / after, as hex, and the backup the vendored write made
            self.assertEqual(err.before, STOCK.hex())
            self.assertEqual(err.expected, build(STOCK, Lighting(mode=3, brightness=2, speed=2)).hex())
            self.assertEqual(err.after, "0100010101010008ffffff")
            self.assertTrue(Path(err.backup).is_file())
            self.assertEqual(load(err.backup)["before"], STOCK.hex())
            text = str(err)
            self.assertIn("Written to the pad", text)
            for hexed in (err.before, err.expected, err.after, err.backup):
                self.assertIn(hexed, text)

    def test_a_write_that_went_out_does_not_say_not_applied_or_paused(self):
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder)
            pad.directory = Path(folder) / "backups"
            pad.stored = bytes.fromhex("0100010101010008ffffff")
            with self.assertRaises(lighting.WriteNotConfirmed) as ctx:
                self.apply(pad, Lighting(mode=3, brightness=2, speed=2), folder)
            text = str(ctx.exception).lower()
            self.assertNotIn("not applied", text)
            self.assertNotIn("paused", text)
            self.assertIn("readback did not match", text)  # the vendored reason stays

    def test_a_failed_check_after_the_write_is_also_a_write_that_went_out(self):
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder)
            pad.directory = Path(folder) / "backups"
            write = pad.write

            def bad_ack(data):
                n = write(data)
                pad.ack = bytes(64)  # the pad answered, wrongly; the payload itself is right
                return n

            pad.write = bad_ack
            with self.assertRaises(lighting.WriteNotConfirmed) as ctx:
                self.apply(pad, Lighting(mode=3, brightness=2, speed=2), folder)
            self.assertEqual(ctx.exception.after, ctx.exception.expected)
            self.assertIn("acknowledgement", str(ctx.exception))

    def test_a_pad_that_cannot_be_read_after_a_write_is_said_so(self):
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder)
            pad.directory = Path(folder) / "backups"
            pad.stored = bytes.fromhex("0100010101010008ffffff")
            real = lighting.read_payload
            calls = []

            def read_payload(reader):
                calls.append(1)
                if len(calls) > 1:  # the read after the failure
                    raise OSError("pad went away")
                return real(reader)

            with mock.patch.object(lighting, "read_payload", read_payload):
                with self.assertRaises(lighting.WriteNotConfirmed) as ctx:
                    self.apply(pad, Lighting(mode=3, brightness=2, speed=2), folder)
            self.assertIsNone(ctx.exception.after)
            self.assertIn("unreadable (pad went away)", str(ctx.exception))

    def test_nothing_sent_is_not_a_write_that_went_out(self):
        # a refusal before the write, and a write call that itself fails, stay plain errors
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder, firmware=104)
            pad.directory = Path(folder) / "backups"
            with self.assertRaises(ValueError) as ctx:
                self.apply(pad, Lighting(mode=2, brightness=4, speed=2), folder)
            self.assertNotIsInstance(ctx.exception, lighting.WriteNotConfirmed)
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder)
            pad.directory = Path(folder) / "backups"

            def refuse(data):
                raise OSError("write failed")

            pad.write = refuse
            with self.assertRaises(RuntimeError) as ctx:
                self.apply(pad, Lighting(mode=3, brightness=2, speed=2), folder)
            self.assertNotIsInstance(ctx.exception, lighting.WriteNotConfirmed)
            self.assertEqual(pad.packets, [])

    def test_out_of_range_lighting_never_reaches_the_pad(self):
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder)
            with self.assertRaises(LightingError):
                self.apply(pad, Lighting(mode=2, brightness=9), folder)
            self.assertEqual(pad.packets, [])

    def test_a_pad_that_is_neither_firmware_100_nor_103_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder, firmware=104)
            pad.directory = Path(folder) / "backups"
            with self.assertRaises(ValueError):
                self.apply(pad, Lighting(mode=2, brightness=4, speed=2), folder)
            self.assertEqual(pad.packets, [])

    def test_firmware_100_still_passes_the_original_check(self):
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder, firmware=100, internal_pid=0x246D)
            pad.directory = Path(folder) / "backups"
            self.assertTrue(
                self.apply(pad, Lighting(mode=2, brightness=4, speed=2), folder)["verified"]
            )

    def test_the_vendored_checks_are_restored_afterwards(self):
        modes = dict(studio.MODES)
        validate = transactions.validate_status
        with tempfile.TemporaryDirectory() as folder:
            pad = FakePad(folder)
            pad.directory = Path(folder) / "backups"
            self.apply(pad, Lighting(mode=7, brightness=4, speed=2), folder)
            pad.stored = bytes(11)
            with self.assertRaises(RuntimeError):
                self.apply(pad, Lighting(mode=3, brightness=1, speed=1), folder)
        self.assertEqual(studio.MODES, modes)
        self.assertIs(transactions.validate_status, validate)
        self.assertEqual(sorted(studio.MODES), [0, 1, 2, 4])


class DataDirTests(unittest.TestCase):
    def test_the_data_folder_is_the_application_folder(self):
        # One definition of the app folder (review finding 13).
        self.assertEqual(lighting.data_dir("/Users/someone"), profile.app_dir("/Users/someone"))
        self.assertEqual(lighting.data_dir(), profile.app_dir())


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.pad = FakePad(self.dir)
        self.pad.directory = self.dir / "backups"
        patcher = mock.patch.object(lighting, "data_dir", return_value=self.dir)
        patcher.start()
        self.addCleanup(patcher.stop)

        @contextmanager
        def connect(directory=None):
            yield self.pad, {"serial_number": "test"}

        patcher = mock.patch.object(lighting, "connect", connect)
        patcher.start()
        self.addCleanup(patcher.stop)

    def profile_file(self, text):
        path = self.dir / "profile.toml"
        path.write_text(text)
        return path

    def run_command(self, answer="y", **kwargs):
        out, err = io.StringIO(), io.StringIO()
        asked = []

        def ask(prompt):
            asked.append(prompt)
            return answer

        code = lighting.lights_command(out=out, err=err, ask=ask, **kwargs)
        return code, out.getvalue(), err.getvalue(), asked

    def test_lights_prints_the_mode_and_writes_nothing(self):
        code, out, err, asked = self.run_command(profile_path=None)
        self.assertEqual(code, 0)
        self.assertIn("pad now: Flow (rows) (mode 4) · brightness 4 · speed 3", out)
        self.assertEqual((self.pad.packets, asked), ([], []))

    def test_lights_with_a_profile_but_no_apply_writes_nothing(self):
        path = self.profile_file("version = 1\n[lighting]\nmode = 2\n")
        code, out, err, asked = self.run_command(profile_path=path)
        self.assertEqual((code, self.pad.packets, asked), (0, [], []))

    def test_apply_shows_the_change_asks_then_writes(self):
        path = self.profile_file(
            "version = 1\n[lighting]\nmode = 2\nbrightness = 4\nspeed = 2\ncolor = [0, 255, 255]\n"
        )
        code, out, err, asked = self.run_command(profile_path=path, apply_changes=True)
        self.assertEqual(code, 0, err)
        self.assertIn("mode: 4 -> 2", out)
        self.assertIn("saved in the pad's memory", out)
        self.assertIn("written and read back", out)
        self.assertEqual(len(asked), 1)
        self.assertEqual(len(self.pad.packets), 1)

    def test_apply_declined_writes_nothing(self):
        path = self.profile_file("version = 1\n[lighting]\nmode = 3\n")
        code, out, err, asked = self.run_command(answer="n", profile_path=path, apply_changes=True)
        self.assertEqual(code, 1)
        self.assertIn("not written", out)
        self.assertEqual(self.pad.packets, [])

    def test_apply_with_nothing_to_change_does_not_ask(self):
        path = self.profile_file("version = 1\n[lighting]\nmode = 4\nbrightness = 4\nspeed = 3\n")
        code, out, err, asked = self.run_command(profile_path=path, apply_changes=True)
        self.assertEqual((code, asked, self.pad.packets), (0, [], []))
        self.assertIn("already set", out)

    def test_apply_without_a_lighting_section_is_an_error(self):
        path = self.profile_file("version = 1\n")
        code, out, err, asked = self.run_command(profile_path=path, apply_changes=True)
        self.assertEqual(code, 2)
        self.assertIn("no [lighting] section", err)
        self.assertEqual(self.pad.packets, [])

    def test_apply_with_a_bad_profile_is_an_error(self):
        path = self.profile_file("version = 1\n[lighting]\nmode = 40\n")
        code, out, err, asked = self.run_command(profile_path=path, apply_changes=True)
        self.assertEqual(code, 2)
        self.assertIn("lighting.mode", err)
        self.assertEqual(self.pad.packets, [])

    def test_a_readback_mismatch_exits_nonzero_with_the_reason(self):
        path = self.profile_file("version = 1\n[lighting]\nmode = 3\n")
        self.pad.stored = bytes.fromhex("0100010101010008ffffff")
        code, out, err, asked = self.run_command(profile_path=path, apply_changes=True)
        self.assertEqual(code, 1)
        self.assertIn("Written to the pad", err)
        self.assertIn("readback did not match", err)
        self.assertNotIn("paused", err)

    def test_the_cli_routes_lights(self):
        from glra_midi import cli

        with (
            mock.patch.object(lighting, "lights_command", return_value=0) as command,
            mock.patch.object(cli, "_migrate_app_dir") as migrate,
        ):
            self.assertEqual(cli.main(["lights", "--apply", "--profile", "x.toml"]), 0)
        migrate.assert_called_once_with()
        command.assert_called_once_with(profile_path="x.toml", apply_changes=True)


if __name__ == "__main__":
    unittest.main()
