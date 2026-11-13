# SPDX-License-Identifier: GPL-3.0-only

"""The pad's factory RGB modes: the mode table, the 11-byte payload and the one guarded write.

Sources: `glean:k16n3-lighting` (probed on Bob's pad, firmware 103, 2026-11-13) and
`docs/config-app.md` section 5. Every `06 0b` write persists to flash, so nothing in this
module writes unless `apply` is called, and `apply` is called only on an explicit request
(`glra-midi lights --apply`, later the app's [Apply to pad]); never from `run` or a profile load.

Payload, 11 bytes: `[1, 0, mode, brightness, speed, direction, colour flag, byte 7, h, s, v]`.
`apply` changes only bytes 2, 3, 4, 6 and 8-10 and keeps the rest (direction, byte 7) as read.
"""

import threading
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path

from .device import lighting as _studio
from .device import transactions as _transactions
from .profile import APP_DIR_NAME

PAYLOAD_SIZE = 11
BRIGHTNESS_RANGE = (0, 4)
SPEED_RANGE = (0, 4)

# Byte positions in the payload.
MODE, BRIGHTNESS, SPEED, DIRECTION, COLOR_FLAG, UNKNOWN_7, HUE, SAT, VAL = (
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
)

# Bob's pad: firmware 103, internal PID 0x2475 (`transactions.fingerprint` order:
# version, internal pid, firmware, profile count, layer count). glra-studio tested 100 only.
BOB_PAD = (1, 0x2475, 103, 6, 1)


@dataclass(frozen=True)
class Mode:
    number: int
    name: str
    brightness: bool  # the mode reads the brightness byte
    speed: bool  # the mode reads the speed byte
    color: bool  # the mode takes colour flag 1 + HSV (one fixed hue)
    # What a probe on 2026-11-13 (Bob watching) settled and what it did not.
    verified: str
    unverified: str = ""


# Verified by eye on 2026-11-13 (`glean:k16n3-lighting`): that each mode number gives the animation
# named in `verified`, and the colour flag + HSV in modes 1, 2, 4-7, 11. NOT verified: direction
# (never offered), which modes read the speed byte (the `speed` column is inferred), the names
# of 4/5 and 9/10 (the probe told the variants apart only as "flows (whole rows/columns)" and
# "Ripples"; the names below are Claude's placeholders), and the colour flag in mode 5 (listed
# with 4, as the finding groups "4-7").
MODES = (
    Mode(0, "Off", False, False, False, "all LEDs dark", "brightness and speed bytes ignored?"),
    Mode(1, "Steady", True, False, True, "gradient, or one hue with the colour flag", "speed"),
    Mode(2, "Breathing", True, True, True, "pulses; one hue with the colour flag"),
    Mode(3, "Spectrum", True, True, False, "colour cycling", "speed; colour flag ignored?"),
    Mode(4, "Flow (rows)", True, True, True, "flows along whole rows", "name; colour flag"),
    Mode(5, "Flow (columns)", True, True, True, "flows along whole columns", "name; colour flag"),
    Mode(6, "Raindrop", True, True, True, "raindrops; one hue with the colour flag"),
    Mode(7, "Meteor", True, True, True, "meteors; one hue with the colour flag"),
    Mode(8, "Starry sky", True, True, False, "twinkling", "speed; colour flag ignored?"),
    Mode(9, "Ripples", True, True, False, "reacts to presses only", "name; speed"),
    Mode(10, "Ripples 2", True, True, False, "reacts to presses only", "name; speed"),
    Mode(11, "Lit on press", True, True, True, "lights on press; one hue with the colour flag"),
    Mode(12, "Custom", True, False, False, "the stored per-key table", "brightness; speed"),
)
MODE_BY_NUMBER = {m.number: m for m in MODES}

# `profile.py` parses `[lighting]` against its own copy of the mode numbers and colour modes;
# `tests/test_lighting.py` checks the two agree.


class LightingError(ValueError):
    """A lighting value or payload that isn't safe to build, send or trust."""


# --- the payload --------------------------------------------------------------------------


@dataclass(frozen=True)
class State:
    """A payload read back into named fields (what the pad holds now)."""

    mode: int
    brightness: int
    speed: int
    direction: int
    color_flag: int
    byte7: int
    hsv: tuple[int, int, int]

    @property
    def color(self):
        return self.hsv if self.color_flag == 1 else None


def parse(payload):
    """Check an 11-byte payload (header `01 00`, a known mode) and name its fields."""
    payload = bytes(payload)
    if len(payload) != PAYLOAD_SIZE:
        raise LightingError(f"lighting payload is {len(payload)} bytes, expected {PAYLOAD_SIZE}")
    if payload[0:2] != b"\x01\x00":
        raise LightingError(f"unexpected lighting header {payload[0:2].hex()}")
    if payload[MODE] not in MODE_BY_NUMBER:
        raise LightingError(f"unknown lighting mode {payload[MODE]}")
    return State(
        mode=payload[MODE],
        brightness=payload[BRIGHTNESS],
        speed=payload[SPEED],
        direction=payload[DIRECTION],
        color_flag=payload[COLOR_FLAG],
        byte7=payload[UNKNOWN_7],
        hsv=(payload[HUE], payload[SAT], payload[VAL]),
    )


def check(lighting):
    """Refuse a `Lighting` the pad shouldn't be sent (also what `profile.py` enforces)."""
    if lighting.mode not in MODE_BY_NUMBER:
        raise LightingError(f"mode {lighting.mode} doesn't exist (0..{len(MODES) - 1})")
    mode = MODE_BY_NUMBER[lighting.mode]
    for what, value, (lo, hi) in (
        ("brightness", lighting.brightness, BRIGHTNESS_RANGE),
        ("speed", lighting.speed, SPEED_RANGE),
    ):
        if type(value) is not int or not lo <= value <= hi:
            raise LightingError(f"{what} must be {lo}..{hi}, got {value!r}")
    if lighting.color is not None:
        if not mode.color:
            raise LightingError(f"{mode.name} (mode {mode.number}) doesn't take a single colour")
        if len(lighting.color) != 3 or any(
            type(v) is not int or not 0 <= v <= 255 for v in lighting.color
        ):
            raise LightingError(
                f"colour must be [h, s, v] with each 0..255, got {lighting.color!r}"
            )


def build(current, lighting):
    """The payload to write: `current` (as read) with `lighting` laid over it.

    Changes only bytes 2, 3, 4, 6 and 8-10. Brightness and speed change only when the mode reads
    them (a mode that ignores a byte keeps the pad's value); the colour flag always follows the
    profile (`color` present = 1, absent = 0); HSV changes only when a colour is given.
    """
    parse(current)
    check(lighting)
    mode = MODE_BY_NUMBER[lighting.mode]
    out = bytearray(current)
    out[MODE] = lighting.mode
    if mode.brightness:
        out[BRIGHTNESS] = lighting.brightness
    if mode.speed:
        out[SPEED] = lighting.speed
    if lighting.color is None:
        out[COLOR_FLAG] = 0
    else:
        out[COLOR_FLAG] = 1
        out[HUE : VAL + 1] = bytes(lighting.color)
    return bytes(out)


def describe(payload):
    """One line for a payload: `Breathing (mode 2) · brightness 4 · speed 2 · colour h0 s255 v255`."""
    state = parse(payload)
    mode = MODE_BY_NUMBER[state.mode]
    parts = [f"{mode.name} (mode {mode.number})"]
    if mode.brightness:
        parts.append(f"brightness {state.brightness}")
    if mode.speed:
        parts.append(f"speed {state.speed}")
    if state.color_flag == 1 and mode.color:
        h, s, v = state.hsv
        parts.append(f"one colour h{h} s{s} v{v}")
    return " · ".join(parts)


def changes(current, new):
    """`[(field, old, new)]` for the bytes that differ, with names (for showing before a write)."""
    old, new = parse(current), parse(new)
    found = []
    for field in ("mode", "brightness", "speed", "direction", "color_flag", "byte7", "hsv"):
        a, b = getattr(old, field), getattr(new, field)
        if a != b:
            found.append((field, a, b))
    return found


# --- reading and the guarded write ---------------------------------------------------------


def read_payload(reader):
    """The pad's current 11 bytes (`06 0a`, an allowlisted read; writes nothing)."""
    raw = reader.query(10)
    if raw[2] != PAYLOAD_SIZE:
        raise LightingError("unexpected lighting response size")
    payload = bytes(raw[5 : 5 + PAYLOAD_SIZE])
    parse(payload)
    return payload


_GATE = threading.Lock()


@contextmanager
def _firmware_103_gate():
    """For one write: glra-studio's checks widened to firmware 103's modes and Bob's pad.

    `glra_midi/device/lighting.py` names only modes 0, 1, 2 and 4, and
    `transactions.validate_status` accepts only firmware 100 / PID 0x246D. The vendored files stay
    as they were; this widens both for the length of the call, as
    `.loom/tied/midi-mvp/unique-assignments.tied/program.py` did for assignment writes.
    Only Bob's fingerprint is added; any other pad goes through the original check.
    """
    original = _transactions.validate_status

    def validate(status):
        if _transactions.fingerprint(status) == BOB_PAD:
            if status["current_profile"] != 0 or status["current_layer"] != 0:
                raise ValueError("Unexpected profile/layer")
            return
        original(status)

    with _GATE:
        saved = dict(_studio.MODES)
        _studio.MODES.update({m.number: m.name for m in MODES})
        _transactions.validate_status = validate
        try:
            yield
        finally:
            _transactions.validate_status = original
            _studio.MODES.clear()
            _studio.MODES.update(saved)


class WriteNotConfirmed(RuntimeError):
    """The `06 0b` went out, but the vendored write could not confirm it.

    Not the same as a refusal: the pad was written, and the pad may now hold what was asked or
    something else. `before`, `expected` and `after` are 11-byte hex strings (`after` is None when
    the pad could not be read again); `backup` is the vendored backup path; `detail` is the
    vendored reason (for example a readback that differed). Nothing here says later writes are
    paused: the app and `lights` stay free to try again, and the user decides.
    """

    def __init__(self, before, expected, after, backup, detail, after_error=""):
        self.before, self.expected, self.after = before, expected, after
        self.backup, self.detail, self.after_error = backup, detail, after_error
        shown = after if after is not None else f"unreadable ({after_error})"
        text = (
            "Written to the pad, but it did not read back as expected. "
            f"Before {before}, expected {expected}, after {shown}."
        )
        if backup:
            text += f" Backup: {backup}."
        if detail:
            text += f" ({detail})"
        super().__init__(text)


class _SentFlag:
    """A reader that notes when its device's `write` has been called and returned.

    Wraps only the attributes `device.lighting.write` uses and passes everything else through, so
    `apply` can tell "refused before anything was sent" from "sent, then not confirmed".
    """

    def __init__(self, reader):
        self._reader = reader
        self.sent = False

    @property
    def device(self):
        return _SentDevice(self._reader.device, self)

    def __getattr__(self, name):
        return getattr(self._reader, name)


class _SentDevice:
    def __init__(self, device, flag):
        self._device, self._flag = device, flag

    def write(self, packet):
        result = self._device.write(packet)
        self._flag.sent = True
        return result

    def __getattr__(self, name):
        return getattr(self._device, name)


_BACKUP_LINE = "Lighting backup: "
_PAUSED = " Further writes are paused."


def _split_vendored_error(text):
    """`(reason, backup path)` from the vendored `RuntimeError` text."""
    reason, _, backup = text.partition("\n" + _BACKUP_LINE)
    return reason.replace(_PAUSED, "").strip(), backup.strip()


def apply(reader, identity, lighting, directory):
    """Lay `lighting` over what the pad holds and write it once, guarded; or write nothing.

    Returns the vendored result dict (`before`, `after`, `backup`, `verified`), plus `unchanged`
    when the pad already held the payload (then nothing is written, not even a backup). Writes
    `06 0b` with 11 bytes only; never `06 14` or `06 12`.

    Raises `WriteNotConfirmed` when the write went out and its check then failed (before /
    expected / after and the backup path are on it); any other error means nothing was sent.
    """
    before = read_payload(reader)
    new = build(before, lighting)
    if new == before:
        return {"before": before.hex(), "after": before.hex(), "unchanged": True}
    watched = _SentFlag(reader)
    with _firmware_103_gate():
        try:
            return _studio.write(watched, identity, new, before.hex(), directory)
        except RuntimeError as exc:
            if not watched.sent:
                raise
            detail, backup = _split_vendored_error(str(exc))
            after = after_error = None
            try:
                after = read_payload(reader).hex()
            except (LightingError, ValueError, RuntimeError, OSError, TimeoutError) as err:
                after_error = str(err)
            raise WriteNotConfirmed(
                before.hex(), new.hex(), after, backup, detail, after_error or ""
            ) from exc


# --- the pad, for the command line (and later the app) -------------------------------------


def data_dir(home=None):
    """Where backups and audit logs go: next to the profile."""
    home = Path.home() if home is None else Path(home)
    return home / "Library" / "Application Support" / APP_DIR_NAME


@contextmanager
def connect(directory=None):
    """Open the pad's vendor interface and yield `(reader, identity)`; closes the audit log after."""
    from .device import backend, storage
    from .device.protocol import Reader

    directory = data_dir() if directory is None else Path(directory)
    identity = backend.select()
    audit = storage.Audit(directory / "logs")
    try:
        with backend.open_device(identity) as device:
            yield Reader(device, audit), identity
    finally:
        with suppress(Exception):
            audit.close()


# --- `glra-midi lights` -----------------------------------------------------------------------


def lights_command(profile_path=None, apply_changes=False, out=None, err=None, ask=input):
    """Print the pad's lighting mode; with `apply_changes`, write the profile's `[lighting]`.

    Writes only after showing the change and getting a "y". Returns an exit code.
    """
    import sys

    from .profile import ProfileError, current_profile_path, load_profile

    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    lighting = None
    if apply_changes:
        path = current_profile_path() if profile_path is None else Path(profile_path)
        try:
            lighting = load_profile(path).lighting
        except ProfileError as exc:
            print(f"glra-midi: {exc}", file=err)
            return 2
        if lighting is None:
            print(f"glra-midi: {path} has no [lighting] section; nothing to apply", file=err)
            return 2
        try:
            check(lighting)
        except LightingError as exc:
            print(f"glra-midi: lighting: {exc}", file=err)
            return 2
    try:
        with connect() as (reader, identity):
            current = read_payload(reader)
            print(f"pad now: {describe(current)}", file=out)
            if lighting is None:
                return 0
            new = build(current, lighting)
            print(f"profile: {describe(new)}", file=out)
            if new == current:
                print("already set; nothing to write", file=out)
                return 0
            for field, old, value in changes(current, new):
                print(f"  {field}: {old} -> {value}", file=out)
            print(
                "Each lighting write is saved in the pad's memory (flash); a backup is made first.",
                file=out,
            )
            if ask("Write this to the pad? [y/N] ").strip().lower() not in ("y", "yes"):
                print("not written", file=out)
                return 1
            result = apply(reader, identity, lighting, data_dir() / "backups")
            if result.get("unchanged"):
                print("already set; nothing written", file=out)
            else:
                print(f"written and read back; backup {result['backup']}", file=out)
            return 0
    except (LightingError, ValueError, RuntimeError, OSError, TimeoutError) as exc:
        print(f"glra-midi: lighting: {exc}", file=err)
        return 1
