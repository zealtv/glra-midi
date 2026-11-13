# SPDX-License-Identifier: GPL-3.0-only

"""Pure engine: ControlEvents + a profile in, raw MIDI messages out.

No I/O and no clock. `Engine.handle(event)` returns a list of `bytes` messages;
`Engine.release_all()` returns what undoes everything still held and forgets that
state. Adapters (rtmidi2 now, OSC later) send or print what comes back. The rules are
in `docs/config-app.md` section 3.

Resolution, on a press or a turn of control C with active layer L: a layer key changes
the layer (and sends nothing); else C's global event; else the event C has on L; else
nothing. There is no fall-through between global and per-layer events (Bob, 2026-11-13).
A release goes to the binding its press started with, whatever the layer is by then.

State: the active layer (starts at 1), a latch per (control, layer) for per-layer
controls and one per global control, and one CC value per (channel, cc) that `cc-set`,
`cc-step`, `cc-momentary` and `cc-absolute` share, seeded from the `initial` of the
absolute dials. Glides (`ease-ms`, `curve`) belong to `cc-easing`: until then every CC
change jumps to its target.

Events for controls the profile leaves out, and the not-yet-identified dials
(`enc.?`), produce nothing.
"""

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

    def handle(self, event):
        kind, _, rest = event.control.partition(".")
        number, _, part = rest.partition(".")
        if not number.isdigit():
            return []
        if (kind == "key" and not part) or (kind == "enc" and part == "push"):
            if event.action == "down":
                return self._press(event.control)
            if event.action == "up":
                return self._release(event.control)
            return []
        if kind == "enc" and not part and event.action in ("cw", "ccw"):
            return self._turn(f"enc.{number}.turn", 1 if event.action == "cw" else -1)
        return []

    def release_all(self):
        """Note Off for every held and latched note, held momentary CCs back to `low`;
        forgets what was held. Latched CCs keep their value and their latch."""
        messages = [m for m in (self._undo(e) for e in self._down.values() if e is not None) if m]
        messages.extend(self._latched_notes.values())
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

    def _press(self, name):
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
            return self._press_cc_momentary(name, binding, action, channel)
        self._down[name] = None
        if isinstance(action, CcSet):
            return [self._send_cc(channel, action.cc, action.value)]  # always sends
        if isinstance(action, CcStep):
            return self._step(channel, action.cc, action.step)
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

    def _press_cc_momentary(self, name, binding, event, channel):
        if event.mode == "latch":
            self._down[name] = None
            if binding in self._latched_ccs:
                self._latched_ccs.discard(binding)
                return [self._send_cc(channel, event.cc, event.low)]
            self._latched_ccs.add(binding)
            return [self._send_cc(channel, event.cc, event.high)]
        self._down[name] = event
        return [self._send_cc(channel, event.cc, event.high)]

    def _step(self, channel, cc, delta):
        old = self._cc.get((channel, cc), 0)
        new = _clamp(old + delta)
        return [] if new == old else [self._send_cc(channel, cc, new)]

    def _release(self, name):
        if name not in self._down:
            return []  # up for something not down
        message = self._undo(self._down.pop(name))
        return [message] if message else []

    def _undo(self, event):
        """The message that releases what `event` started (None: nothing to undo)."""
        if event is None:
            return None
        channel = self._channel(event)
        if isinstance(event, Note):
            return bytes([NOTE_OFF | channel, event.note, 0])
        return self._send_cc(channel, event.cc, event.low)

    # --- encoder turns ---------------------------------------------------------------------

    def _turn(self, name, delta):
        _, action = self._resolve(name)
        if isinstance(action, CcAbsolute):
            return self._step(self._channel(action), action.cc, delta * action.step)
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
