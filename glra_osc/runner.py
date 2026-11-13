# SPDX-License-Identifier: GPL-3.0-only

"""`glra-osc run`: pad reports -> decoder -> engine -> virtual MIDI port (or stdout).

The rtmidi2 part is `MidiPort`, a few lines around `MidiOut`. Everything else
is the pure engine plus the `monitor.watch` loop. Held notes are released on
Ctrl-C, SIGTERM and pad disconnect. The pad is silenced through `silence.py` (a
hidutil key mapping) and restored on exit; nothing is written to the pad's memory.
"""

import signal
import sys

from .decode import Decoder
from .engine import Engine, describe
from .mapping import load_mapping
from .monitor import watch
from .profile import profile_from_mapping
from .silence import Guard, SilenceError, Silencer, TYPING_WARNING, refusal_message


class MidiPort:
    """A virtual CoreMIDI output; DAWs see it as a source named `name`."""

    def __init__(self, name):
        import rtmidi2

        self._out = rtmidi2.MidiOut()
        self._out.open_virtual_port(name)

    def send(self, message):
        self._out.send_raw(*message)

    def close(self):
        self._out.close_port()


class DryRunPort:
    """Prints what a `MidiPort` would send."""

    def __init__(self, out):
        self._out = out

    def send(self, message):
        print("MIDI " + describe(message), file=self._out, flush=True)

    def close(self):
        pass


def _terminate(signum, frame):
    raise KeyboardInterrupt  # same exit path as Ctrl-C


def run(config=None, dry_run=False, out=None, err=None, allow_typing=False, silencer=None):
    out, err = out or sys.stdout, err or sys.stderr
    mapping = load_mapping(config)  # MappingError propagates to the CLI
    if allow_typing:
        print(TYPING_WARNING, file=err, flush=True)

    decoder = Decoder()
    # Until runner-profile loads profiles directly: a legacy mapping as a one-layer profile.
    engine = Engine(profile_from_mapping(mapping))
    port = DryRunPort(out) if dry_run else MidiPort(mapping.port)

    def say(text):
        print(text, file=out, flush=True)

    def send_all(messages):
        for message in messages:
            port.send(message)

    def on_report(source, data, t, wall):
        for event in decoder.feed(source, data, t):
            send_all(engine.handle(event))

    guard = Guard(silencer or Silencer(decoder.layout), say, allow_typing)
    code = 0
    previous = signal.signal(signal.SIGTERM, _terminate)
    try:
        if decoder.layout["provisional"]:
            say("# layout is provisional: dials decode as 'enc.?' and send no MIDI yet")
        say(f"# {'dry run, no port opened' if dry_run else 'virtual port ' + repr(mapping.port)}")
        watch(
            decoder,
            on_report,
            say,
            on_lost=lambda: send_all(engine.release_all()),
            on_pad=guard.on_pad,
            on_tick=guard.tick,
        )
    except SilenceError as exc:
        print(refusal_message(exc), file=err, flush=True)
        code = 1
    finally:
        signal.signal(signal.SIGTERM, previous)
        send_all(engine.release_all())
        port.close()
        guard.close()
    return code
