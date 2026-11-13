# SPDX-License-Identifier: GPL-3.0-only

"""The pad, as the app sees it: two reads-and-one-write calls behind a small interface.

`docs/config-app.md` 4.10 and 5.3. The controller holds a *pad object* and never opens a device
itself, so tests, `--demo` and every capture pass a `FakePad` and no real HID call can happen.
Only `RealPad` (made by `gui.main` when it is not in `--demo`) reaches the device:

- `read()` is read-only: the pad's status (firmware) and its 11 lighting bytes (`06 0a`).
- `apply(lighting, directory)` is the one guarded write (`glra_midi.lighting.apply`: read,
  backup, `06 0b`, readback that ignores what firmware 103 normalises). It runs only when the controller is told to by an explicit
  [Apply to pad] click; nothing here calls it on its own.

Both calls block, so the controller runs them on `padworker.PadWorker`'s thread, as
glra-studio's `worker.py` keeps its device transactions on one worker thread.
"""

from dataclasses import dataclass
from pathlib import Path

from .. import lighting as lights

# The pad as a probe on 2026-11-13 found it (`glean:k16n3-lighting`): stock Flow (rows),
# brightness 4, speed 3, direction 3, byte 7 = 8, colour flag 0, HSV ff ff ff.
STOCK_PAYLOAD = bytes.fromhex("0100040403030008ffffff")
STOCK_FIRMWARE = 103

# What a failed pad call can raise (the same list `lights_command` catches).
PAD_ERRORS = (lights.LightingError, ValueError, RuntimeError, OSError, TimeoutError, ImportError)


@dataclass(frozen=True)
class PadReading:
    """What one read found. `connected` False: no pad answered (`detail` says what failed)."""

    connected: bool
    firmware: int | None = None
    payload: bytes | None = None
    detail: str = ""


@dataclass(frozen=True)
class ApplyResult:
    """What one Apply did. `unchanged`: the pad already held it, nothing was written."""

    unchanged: bool
    payload: bytes  # the pad's lighting bytes afterwards
    backup: str = ""


def not_found(detail=""):
    return PadReading(connected=False, detail=detail)


class NoPad:
    """No pad object at all (a Controller made without one): never connected, never any I/O."""

    def read(self):
        return not_found("No pad connection in this session.")

    def apply(self, lighting, directory):
        raise RuntimeError("No pad to write to.")


class FakePad:
    """A pad that lives in memory: records every call, holds a lighting payload.

    `--demo`, the captures and the tests use this. `apply` behaves as `lighting.apply` does: it
    lays the profile's lighting over the held payload with `lighting.build`, writes nothing when
    that changes nothing, and otherwise counts one write. `connected=False` answers "not found".
    `error` makes the next calls raise it (a readback mismatch, say).
    """

    def __init__(self, payload=STOCK_PAYLOAD, firmware=STOCK_FIRMWARE, connected=True):
        self.payload = bytes(payload)
        self.firmware = firmware
        self.connected = connected
        self.error = None
        self.reads = 0
        self.apply_calls = []  # one (Lighting, directory) per `apply` call
        self.writes = []  # one payload per write that changed the pad

    def read(self):
        self.reads += 1
        if not self.connected:
            return not_found("Expected one matching interface, found 0.")
        return PadReading(True, self.firmware, self.payload)

    def apply(self, lighting, directory):
        self.apply_calls.append((lighting, directory))
        if not self.connected:
            raise ValueError("Expected one matching interface, found 0.")
        if self.error is not None:
            raise self.error
        new = lights.build(self.payload, lighting)
        if new == self.payload:
            return ApplyResult(True, self.payload)
        self.writes.append(new)
        self.payload = new
        return ApplyResult(False, new, backup=str(Path(directory) / "fake-lighting-before.json"))


def load_hidapi():
    """Import the `hid` module now, on the calling thread (the UI thread, for `RealPad()`).

    `import hid` initialises hidapi, and on macOS that attaches its IOHIDManager to the run
    loop of the thread doing the import. `glra_midi.device.backend` imports `hid` lazily, so
    the first import would otherwise happen on the pad worker thread. At interpreter exit the
    `hid` module's exit hook closes the manager on the main thread, where it walks that
    thread's long-dead run loop and the process dies with EXC_BREAKPOINT ("Python quit
    unexpectedly", `fix-quit-crash`, 2026-11-13). Importing here, on the main thread, ties
    the manager to a run loop that lives until exit. A failed import is left for `read` to
    report as "Pad: not found" (`ImportError` is in `PAD_ERRORS`).
    """
    try:
        import hid  # noqa: F401
    except ImportError:
        pass


class RealPad:
    """The real pad, through `glra_midi.lighting`. Built only by `gui.main` outside `--demo`.

    Each call opens the vendor interface non-exclusively, does its work and closes it, so it
    does not hold the pad while `glra-midi run` plays (whether a read still answers then needs
    the real pad to find out; the stitch's report says so).
    """

    def __init__(self, data_directory=None):
        self.data_directory = data_directory
        load_hidapi()

    def read(self):
        try:
            with lights.connect(self.data_directory) as (reader, _identity):
                payload = lights.read_payload(reader)
                try:
                    firmware = reader.status()["firmware"]
                except PAD_ERRORS:
                    firmware = None
        except PAD_ERRORS as err:
            return not_found(str(err))
        return PadReading(True, firmware, payload)

    def apply(self, lighting, directory):
        with lights.connect(self.data_directory) as (reader, identity):
            result = lights.apply(reader, identity, lighting, directory)
        after = bytes.fromhex(result["after"])
        return ApplyResult(bool(result.get("unchanged")), after, str(result.get("backup", "")))


def describe_reading(reading):
    """`(headline, now)`: `"Pad: connected (103)"` and the mode line, or `"Pad: not found"`."""
    if not reading.connected:
        return "Pad: not found", ""
    firmware = f" ({reading.firmware})" if reading.firmware is not None else ""
    now = ""
    if reading.payload is not None:
        try:
            now = lights.describe(reading.payload)
        except lights.LightingError as err:
            now = f"unreadable: {err}"
    return f"Pad: connected{firmware}", now
