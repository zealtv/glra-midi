# SPDX-License-Identifier: GPL-3.0-only

"""Pure engine: ControlEvents + a profile in, raw MIDI messages out.

No I/O and no clock of its own: time comes in through `event.t` and `tick(now)`.
`Engine.handle(event)` returns a list of `bytes` messages; `Engine.tick(now)` returns the
glide messages due; `Engine.next_due()` says when to call `tick` again (None: nothing
glides); `Engine.release_all()` returns what undoes everything still held and forgets that
state. Adapters (rtmidi2 now, OSC later) send or print what comes back. The rules are
in `docs/config-app.md` section 3.

Resolution, on a press or a turn of control C with active layer L: a layer key changes
the layer (and sends nothing); else C's global event; else the event C has on L; else
nothing. There is no fall-through between global and per-layer events (Bob, 2026-11-13).
A release goes to the binding its press started with, whatever the layer is by then.

State: the active layer (starts at 1), a latch per (control, layer) for per-layer
controls and one per global control, and one CC value per (channel, cc) that `cc-set`,
`cc-step`, `cc-momentary` and `cc-absolute` share, seeded from the `initial` of the
absolute dials.

Glides (section 3.6): a `cc-momentary` press glides to `high` over `rise-ms` and its release
back to `low` over `fall-ms`; a `cc-step` glides over `ease-ms`; all along `curve`. One glide
per (channel, cc): a later glide, a `cc-set` or an absolute turn on the same pair replaces
it. A time of 0 jumps from `handle` itself. `tick` runs at 100 Hz while a glide runs and sends
only when the rounded 7-bit value changes.

Events for controls the profile leaves out, and the not-yet-identified dials
(`enc.?`), produce nothing.
"""

import math
from dataclasses import dataclass

from .profile import (
    CcAbsolute,
    CcMomentary,
    CcRelative,
    CcSet,
    CcStep,
    LayerDec,
    LayerInc,
    LayerSet,
    Note,
    PerLayer,
)

NOTE_OFF, NOTE_ON, CONTROL_CHANGE = 0x80, 0x90, 0xB0


def _relative_value(encoding, delta):
    """CC data byte for a one-detent turn (delta is +1 or -1)."""
    if encoding == "twos-complement":
        return delta & 0x7F  # +1 -> 1, -1 -> 127
    if encoding == "binary-offset":
        return 64 + delta
    return 1 if delta > 0 else 0x41  # signed-bit: bit 6 is the sign


def _clamp(value):
    return max(0, min(127, value))


TICK = 0.010  # seconds between glide ticks (100 Hz)
_EPSILON = 1e-9  # slack so a tick that lands on the end time (up to float error) ends the glide

# Easing curves on progress p in 0..1 (docs/config-app.md 3.6).
CURVES = {
    "linear": lambda p: p,
    "ease-in": lambda p: p * p,
    "ease-out": lambda p: 1 - (1 - p) ** 2,
    "ease-in-out": lambda p: 2 * p * p if p < 0.5 else 1 - 2 * (1 - p) ** 2,
}


@dataclass
class _Glide:
    """One running glide on a (channel, cc): start and target values, start time, seconds."""

    start: int
    target: int
    t0: float
    duration: float
    curve: str

    def value(self, now):
        p = min(1.0, max(0.0, (now - self.t0) / self.duration))
        return int(math.floor(self.start + (self.target - self.start) * CURVES[self.curve](p) + 0.5))

    def done(self, now):
        return now >= self.t0 + self.duration - _EPSILON


class Engine:
    def __init__(self, profile, layer=1, on_layer=None):
        """`layer` is where to start (1 if it doesn't exist in this profile); `on_layer`,
        when given, is called as `on_layer(old, new)` after every layer change."""
        self.profile = profile
        self.on_layer = on_layer
        self._layer = layer if 1 <= layer <= profile.layer_count else 1
        # control name -> what its release undoes (the event), or None when it needs nothing
        self._down = {}
        # (control, layer or None) -> Note Off message, for latched notes that are on
        self._latched_notes = {}
        # (control, layer or None) for latched CC momentaries that sit at `high`
        self._latched_ccs = set()
        # (channel 0..15, cc) -> last value; absolute dials seed it from `initial`
        self._cc = {}
        # (channel 0..15, cc) -> the running _Glide; insertion order is tick order
        self._glides = {}
        self._next_due = None
        for control in profile.controls.values():
            events = (e for _, e in control.events) if isinstance(control, PerLayer) else (control,)
            for event in events:
                if isinstance(event, CcAbsolute) and event.initial is not None:
                    self._cc.setdefault((self._channel(event), event.cc), event.initial)

    @property
    def layer(self):
        """The active layer, 1-based."""
        return self._layer

    @property
    def held(self):
        """Control names currently holding a note or momentary CC."""
        return sorted(name for name, event in self._down.items() if event is not None)

    def cc_value(self, channel, cc):
        """The shared value for (channel 1..16, cc): what the engine last sent or was seeded with."""
        return self._cc.get((channel - 1, cc), 0)

    def next_due(self):
        """When to call `tick` next (a time on the event clock), or None when nothing glides."""
        return self._next_due

    def tick(self, now):
        """Messages the running glides owe at `now`: one per (channel, cc) at most, sent only
        when the rounded value changed; a glide that has run its time ends exactly on its target."""
        messages = []
        for key, glide in list(self._glides.items()):
            value = glide.target if glide.done(now) else glide.value(now)
            if glide.done(now):
                del self._glides[key]
            if value != self._cc.get(key, 0):
                messages.append(self._send_cc(key[0], key[1], value))
        self._next_due = now + TICK if self._glides else None
        return messages

    def handle(self, event):
        kind, _, rest = event.control.partition(".")
        number, _, part = rest.partition(".")
        if not number.isdigit():
            return []
        if (kind == "key" and not part) or (kind == "enc" and part == "push"):
            if event.action == "down":
                return self._press(event.control, event.t)
            if event.action == "up":
                return self._release(event.control, event.t)
            return []
        if kind == "enc" and not part and event.action in ("cw", "ccw"):
            return self._turn(f"enc.{number}.turn", 1 if event.action == "cw" else -1)
        return []

    def release_all(self):
        """Note Off for every held and latched note; held momentary CCs jump to `low` and every
        other running glide jumps to its target; forgets what was held. Latched CCs keep their
        value and their latch."""
        messages = [m for m in (self._undo(e) for e in self._down.values() if e is not None) if m]
        messages.extend(self._latched_notes.values())
        for key, glide in self._glides.items():
            if glide.target != self._cc.get(key, 0):
                messages.append(self._send_cc(key[0], key[1], glide.target))
        self._glides.clear()
        self._next_due = None
        self._down.clear()
        self._latched_notes.clear()
        return messages

    # --- resolution ------------------------------------------------------------------------

    def _resolve(self, name):
        """(binding, action) for control `name` now; binding is (name, layer or None)."""
        control = self.profile.controls.get(name)
        if control is None:
            return None, None
        if isinstance(control, PerLayer):
            return (name, self._layer), control.get(self._layer)
        return (name, None), control

    def _channel(self, event):
        """The event's MIDI channel as 0..15."""
        return (event.channel or self.profile.channel) - 1

    def _send_cc(self, channel, cc, value):
        self._cc[(channel, cc)] = value
        return bytes([CONTROL_CHANGE | channel, cc, value])

    def _cancel(self, key):
        """Drop the glide on (channel, cc), if any; no glides left means no tick is due."""
        self._glides.pop(key, None)
        if not self._glides:
            self._next_due = None

    def _move(self, channel, cc, target, ms, curve, t, always=False):
        """Take (channel, cc) to `target` over `ms`, replacing any glide on it; messages due now.

        0 ms jumps: the message goes out now (always when `always`, else only on a change).
        Longer starts a glide from the value last sent and sends nothing yet."""
        key = (channel, cc)
        current = self._cc.get(key, 0)
        self._cancel(key)
        if ms <= 0:
            return [self._send_cc(channel, cc, target)] if always or target != current else []
        if target != current:
            self._glides[key] = _Glide(current, target, t, ms / 1000, curve)
            if self._next_due is None:
                self._next_due = t + TICK
        return []

    # --- layers ----------------------------------------------------------------------------

    def _change_layer(self, action):
        count = self.profile.layer_count
        if isinstance(action, LayerSet):
            new = action.layer if 1 <= action.layer <= count else self._layer
        elif isinstance(action, LayerInc):
            new = self._layer % count + 1
        else:
            new = (self._layer - 2) % count + 1
        old, self._layer = self._layer, new
        if new != old and self.on_layer is not None:
            self.on_layer(old, new)

    # --- presses ---------------------------------------------------------------------------

    def _press(self, name, t):
        if name in self._down:
            return []  # repeated down
        binding, action = self._resolve(name)
        if action is None:
            return []
        if isinstance(action, (LayerSet, LayerInc, LayerDec)):
            self._down[name] = None
            self._change_layer(action)
            return []
        channel = self._channel(action)
        if isinstance(action, Note):
            return self._press_note(name, binding, action, channel)
        if isinstance(action, CcMomentary):
            return self._press_cc_momentary(name, binding, action, channel, t)
        self._down[name] = None
        if isinstance(action, CcSet):
            self._cancel((channel, action.cc))  # a set value cancels a glide and wins
            return [self._send_cc(channel, action.cc, action.value)]  # always sends
        if isinstance(action, CcStep):
            return self._press_cc_step(channel, action, t)
        return []

    def _press_note(self, name, binding, note, channel):
        if note.mode == "latch":
            self._down[name] = None
            if binding in self._latched_notes:
                return [self._latched_notes.pop(binding)]
            self._latched_notes[binding] = bytes([NOTE_OFF | channel, note.note, 0])
            return [bytes([NOTE_ON | channel, note.note, note.velocity])]
        self._down[name] = note
        return [bytes([NOTE_ON | channel, note.note, note.velocity])]

    def _press_cc_momentary(self, name, binding, event, channel, t):
        if event.mode == "latch":
            self._down[name] = None
            if binding in self._latched_ccs:
                self._latched_ccs.discard(binding)
                return self._move(channel, event.cc, event.low, event.fall_ms, event.curve, t, True)
            self._latched_ccs.add(binding)
            return self._move(channel, event.cc, event.high, event.rise_ms, event.curve, t, True)
        self._down[name] = event
        return self._move(channel, event.cc, event.high, event.rise_ms, event.curve, t, True)

    def _press_cc_step(self, channel, event, t):
        """Move the target by `step` (clamped); a running glide's target is the base, so
        quick presses build on each other, and the new glide starts from the value sent."""
        glide = self._glides.get((channel, event.cc))
        base = glide.target if glide else self._cc.get((channel, event.cc), 0)
        return self._move(channel, event.cc, _clamp(base + event.step), event.ease_ms, event.curve, t)

    def _release(self, name, t):
        if name not in self._down:
            return []  # up for something not down
        event = self._down.pop(name)
        if isinstance(event, CcMomentary):
            return self._move(self._channel(event), event.cc, event.low, event.fall_ms, event.curve, t, True)
        message = self._undo(event)
        return [message] if message else []

    def _undo(self, event):
        """The message that releases what `event` started now (None: nothing to undo)."""
        if event is None:
            return None
        channel = self._channel(event)
        if isinstance(event, Note):
            return bytes([NOTE_OFF | channel, event.note, 0])
        self._cancel((channel, event.cc))
        return self._send_cc(channel, event.cc, event.low)

    # --- encoder turns ---------------------------------------------------------------------

    def _step(self, channel, cc, delta):
        """Absolute dial: the shared value plus `delta`, clamped; sent only on a change."""
        old = self._cc.get((channel, cc), 0)
        new = _clamp(old + delta)
        return [] if new == old else [self._send_cc(channel, cc, new)]

    def _turn(self, name, delta):
        _, action = self._resolve(name)
        if isinstance(action, CcAbsolute):
            channel = self._channel(action)
            self._cancel((channel, action.cc))  # a dial turn cancels a glide and wins
            return self._step(channel, action.cc, delta * action.step)
        if isinstance(action, CcRelative):
            value = _relative_value(action.encoding, delta)
            return [bytes([CONTROL_CHANGE | self._channel(action), action.cc, value])]
        return []


def describe(message):
    """Human-readable form of a message the engine produces, for `--dry-run`."""
    status, a, b = message[0] & 0xF0, message[1], message[2]
    channel = (message[0] & 0x0F) + 1
    name = {NOTE_ON: "note on ", NOTE_OFF: "note off", CONTROL_CHANGE: "cc      "}[status]
    label = "value" if status == CONTROL_CHANGE else "vel"
    return f"{message.hex(' ')}  ch {channel:<2} {name} {a:<3} {label} {b}"
