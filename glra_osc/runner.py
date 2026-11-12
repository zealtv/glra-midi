# SPDX-License-Identifier: GPL-3.0-only

"""`glra-osc run`: pad reports -> decoder -> engine -> virtual MIDI port (or stdout).

The rtmidi2 part is `MidiPort`, a few lines around `MidiOut`. Everything else
is the pure engine plus the `monitor.watch` loop. Held notes are released on
Ctrl-C, SIGTERM and pad disconnect. Nothing is written to the pad.
"""

import signal
import sys

from .decode import Decoder
from .engine import Engine, describe
from .mapping import load_mapping
from .monitor import watch

SUPPRESSION_WARNING = (
    "WARNING: silent-capture has not landed yet, so the pad still types into the focused app\n"
    "         (keys send their numpad characters, dials change the volume) while it plays MIDI."
)


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


def run(config=None, dry_run=False, out=None, err=None):
    out, err = out or sys.stdout, err or sys.stderr
    mapping = load_mapping(config)  # MappingError propagates to the CLI
    print(SUPPRESSION_WARNING, file=err, flush=True)

    decoder = Decoder()
    engine = Engine(mapping)
    port = DryRunPort(out) if dry_run else MidiPort(mapping.port)

    def say(text):
        print(text, file=out, flush=True)

    def send_all(messages):
        for message in messages:
            port.send(message)

    def on_report(source, data, t, wall):
        for event in decoder.feed(source, data, t):
            send_all(engine.handle(event))

    previous = signal.signal(signal.SIGTERM, _terminate)
    try:
        if decoder.layout["provisional"]:
            say("# layout is provisional: dials decode as 'enc.?' and send no MIDI yet")
        say(f"# {'dry run, no port opened' if dry_run else 'virtual port ' + repr(mapping.port)}")
        watch(decoder, on_report, say, on_lost=lambda: send_all(engine.release_all()))
    finally:
        signal.signal(signal.SIGTERM, previous)
        send_all(engine.release_all())
        port.close()
    return 0
