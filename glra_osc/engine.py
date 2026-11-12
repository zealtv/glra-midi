# SPDX-License-Identifier: GPL-3.0-only

"""Pure engine: ControlEvents + mapping in, raw MIDI messages out.

No I/O and no clock. `Engine.handle(event)` returns a list of `bytes` messages;
`Engine.release_all()` returns what undoes everything still held (Note Off for
held notes, the "off" value for held momentary CCs) and forgets that state. Adapters
(rtmidi2 now, OSC later) send or print what comes back.

Events for controls the mapping leaves out, and the not-yet-identified dials
(`enc.?`), produce nothing.
"""

from .mapping import AbsoluteTurn, NoteBinding

NOTE_OFF, NOTE_ON, CONTROL_CHANGE = 0x80, 0x90, 0xB0


def _relative_value(encoding, delta):
    """CC data byte for a one-detent turn (delta is +1 or -1)."""
    if encoding == "twos-complement":
        return delta & 0x7F  # +1 -> 1, -1 -> 127
    if encoding == "binary-offset":
        return 64 + delta
    return 1 if delta > 0 else 0x41  # signed-bit: bit 6 is the sign


class Engine:
    def __init__(self, mapping):
        self.mapping = mapping
        self._ch = mapping.midi_channel
        self._toggled = set()  # control names of toggle bindings that are on
        self._held = {}  # control name -> message that releases it
        self._absolute = {
            n: turn.initial
            for n, turn in mapping.enc_turn.items()
            if isinstance(turn, AbsoluteTurn)
        }

    @property
    def held(self):
        """Control names currently holding a note or momentary CC."""
        return sorted(self._held)

    def handle(self, event):
        kind, _, rest = event.control.partition(".")
        number, _, part = rest.partition(".")
        if not number.isdigit():
            return []
        number = int(number)
        if kind == "key" and not part:
            binding = self.mapping.keys.get(number)
        elif kind == "enc" and part == "push":
            binding = self.mapping.enc_push.get(number)
        elif kind == "enc" and not part:
            return self._turn(number, event.action)
        else:
            return []
        if binding is None or event.action not in ("down", "up"):
            return []
        return self._button(event.control, binding, event.action == "down")

    def release_all(self):
        messages = list(self._held.values())
        self._toggled.difference_update(self._held)  # released toggles are off again
        self._held.clear()
        return messages

    # --- buttons -------------------------------------------------------------------------

    def _button(self, control, binding, down):
        if binding.mode == "toggle":
            if not down:
                return []
            on = control not in self._toggled
            self._toggled.symmetric_difference_update({control})
        elif down == (control in self._held):
            return []  # repeated down, or up for something not held
        else:
            on = down
        # Notes and momentary CCs get released on exit; a toggled CC keeps its value.
        if on and (isinstance(binding, NoteBinding) or binding.mode == "momentary"):
            self._held[control] = self._message(binding, False)
        else:
            self._held.pop(control, None)
        return [self._message(binding, on)]

    def _message(self, binding, on):
        if isinstance(binding, NoteBinding):
            status = NOTE_ON if on else NOTE_OFF
            return bytes([status | self._ch, binding.note, binding.velocity if on else 0])
        return bytes([CONTROL_CHANGE | self._ch, binding.cc, binding.on if on else binding.off])

    # --- encoder turns -------------------------------------------------------------------

    def _turn(self, number, action):
        turn = self.mapping.enc_turn.get(number)
        if turn is None or action not in ("cw", "ccw"):
            return []
        delta = 1 if action == "cw" else -1
        if isinstance(turn, AbsoluteTurn):
            old = self._absolute[number]
            value = max(0, min(127, old + delta * turn.step))
            if value == old:
                return []
            self._absolute[number] = value
        else:
            value = _relative_value(turn.encoding, delta)
        return [bytes([CONTROL_CHANGE | self._ch, turn.cc, value])]


def describe(message):
    """Human-readable form of a message the engine produces, for `--dry-run`."""
    status, a, b = message[0] & 0xF0, message[1], message[2]
    channel = (message[0] & 0x0F) + 1
    name = {NOTE_ON: "note on ", NOTE_OFF: "note off", CONTROL_CHANGE: "cc      "}[status]
    label = "value" if status == CONTROL_CHANGE else "vel"
    return f"{message.hex(' ')}  ch {channel:<2} {name} {a:<3} {label} {b}"
