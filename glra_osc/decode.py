# SPDX-License-Identifier: GPL-3.0-only

"""Pure decoder: HID input report bytes in, ControlEvents out.

The pad reports on two interfaces (see glean k16n3-hid-interfaces):
- "keys" (interface 0): boot keyboard report `mod 00 k1..k6`. Press and release
  both arrive as real reports; a release is the usage vanishing from the list.
- "consumer" (interface 1): `03 lo hi`. A dial turn is a press plus an
  immediate `03 00 00`; the turn counts at the press. A push is a press that
  stays until `03 00 00` arrives when the button is let go.
"""

import json
from importlib import resources

from .events import ControlEvent

SOURCES = ("keys", "consumer")
_ROLLOVER_ERROR = 0x01  # boot-protocol "too many keys" fill


def load_layout(path=None):
    """Load layout.json (the packaged default, or `path`)."""
    if path is None:
        text = resources.files("glra_osc.device").joinpath("layout.json").read_text("utf-8")
    else:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    raw = json.loads(text)
    return {
        "provisional": raw.get("provisional", False),
        "keys": {int(k, 16): v for k, v in raw["keys"].items()},
        "consumer": {int(k, 16): v for k, v in raw["consumer"].items()},
    }


class Decoder:
    """Stateful because key releases and dial pushes arrive as "usage gone"."""

    def __init__(self, layout=None):
        self.layout = layout or load_layout()
        self._keys_down = set()
        self._push_down = None  # control name of a dial push being held

    def reset(self):
        """Forget held state (call after an unplug)."""
        self._keys_down.clear()
        self._push_down = None

    def feed(self, source, report, t):
        if source == "keys":
            return self._keys(bytes(report), t)
        if source == "consumer":
            return self._consumer(bytes(report), t)
        raise ValueError(f"unknown source {source!r}")

    def _name(self, usage):
        return self.layout["keys"].get(usage, f"key.unknown:{usage:#04x}")

    def _keys(self, report, t):
        if len(report) < 3:
            return []
        usages = {u for u in report[2:8] if u > _ROLLOVER_ERROR}
        if any(u == _ROLLOVER_ERROR for u in report[2:8]):
            return []  # phantom state: no information, keep what we hold
        events = [
            ControlEvent(self._name(u), "up", t) for u in sorted(self._keys_down - usages)
        ] + [ControlEvent(self._name(u), "down", t) for u in sorted(usages - self._keys_down)]
        self._keys_down = usages
        return events

    def _consumer(self, report, t):
        if len(report) < 3 or report[0] != 3:
            return []
        usage = report[1] | report[2] << 8
        events = []
        if self._push_down is not None:
            # Release, or another usage replacing the push (seen once in capture).
            events.append(ControlEvent(self._push_down, "up", t))
            self._push_down = None
        if usage == 0:
            return events
        entry = self.layout["consumer"].get(usage)
        if entry is None:
            events.append(ControlEvent(f"consumer.unknown:{usage:#06x}", "down", t))
        elif entry["kind"] == "turn":
            events.append(ControlEvent(entry["control"], entry["action"], t))
        else:
            self._push_down = entry["control"]
            events.append(ControlEvent(entry["control"], "down", t))
        return events
