# SPDX-License-Identifier: GPL-3.0-only

"""`glra-midi run`: pad reports -> decoder -> engine -> virtual MIDI port (or stdout).

The rtmidi2 part is `MidiPort`, a few lines around `MidiOut`. Everything else
is the pure engine plus the `monitor.watch` loop. Held notes are released on
Ctrl-C, SIGTERM and pad disconnect. The pad is silenced through `silence.py` (a
hidutil key mapping) and restored on exit; nothing is written to the pad's memory.
"""

import os
import signal
import sys
import time

from .decode import Decoder
from .engine import Engine, describe
from .events import format_event
from .monitor import watch
from .profile import ProfileError, current_profile_path, load_profile
from .silence import Guard, SilenceError, Silencer, TYPING_WARNING, refusal_message

TICK_SLACK = 1e-6  # seconds; a wake this close before a glide tick is due still sends it
RELOAD_POLL_SECONDS = 0.5  # how often to look for a changed profile file or `current` pointer


def _stamp(path):
    """What identifies this version of a file: mtime, inode (the app saves by rename) and size."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_ino, st.st_size)


class ProfileSource:
    """Which profile file `run` plays, and whether it changed since `poll` last said so.

    With `config`, that one file. Without, `current_profile_path()` each time: the `current`
    pointer is followed, so switching profile in the app switches what `run` plays (design 2).
    """

    def __init__(self, config=None, home=None):
        self._config, self._home = config, home
        self.path = self._locate()
        self.seen = (self.path, _stamp(self.path))

    def _locate(self):
        return self._config or current_profile_path(self._home)

    def poll(self):
        """The path to reload when the file or the pointer's target changed, else None."""
        path = self._locate()
        now = (path, _stamp(path))
        if now == self.seen:
            return None
        self.seen = now
        return path


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


def run(
    config=None,
    dry_run=False,
    out=None,
    err=None,
    allow_typing=False,
    silencer=None,
    clock=time.monotonic,
    home=None,
):
    """Play a profile: `config` (a file) or, without it, the one `current` names.

    `ProfileError` from the first load propagates to the CLI before anything opens. Later,
    a changed file or pointer is reloaded; an invalid one keeps the old profile.
    """
    out, err = out or sys.stdout, err or sys.stderr
    source = ProfileSource(config, home)
    profile = load_profile(source.path)
    if allow_typing:
        print(TYPING_WARNING, file=err, flush=True)

    decoder = Decoder()
    port_name = profile.port
    port = DryRunPort(out) if dry_run else MidiPort(port_name)

    def say(text):
        print(text, file=out, flush=True)

    def on_layer(old, new):
        if dry_run:
            names = state["profile"].layer_names
            name = names[new - 1] if new <= len(names) else ""
            say(f"# layer {old} -> {new}" + (f" {name!r}" if name else ""))

    state = {"engine": Engine(profile, on_layer=on_layer), "profile": profile}

    def send_all(messages):
        for message in messages:
            port.send(message)

    def on_report(source_name, data, t, wall):
        engine = state["engine"]
        for event in decoder.feed(source_name, data, t):
            if dry_run:
                say(format_event(event, wall, state["profile"].orientation))
            send_all(engine.handle(event))

    poll_at = clock() + RELOAD_POLL_SECONDS
    failed = {"stamp": None}  # the invalid file's stamp, so its error prints once

    def reload():
        path = source.poll()
        if path is None:
            return
        try:
            new = load_profile(path)
        except ProfileError as exc:
            if failed["stamp"] != source.seen:
                failed["stamp"] = source.seen
                say(f"# profile not reloaded, keeping the old one: {exc}")
            return
        failed["stamp"] = None
        old_engine = state["engine"]
        send_all(old_engine.release_all())  # nothing held or gliding crosses the swap (3.7)
        state["profile"] = new
        state["engine"] = Engine(new, layer=old_engine.layer, on_layer=on_layer, carry=old_engine)
        say(f"# reloaded {path}")
        if new.port != port_name:
            say(f"# port stays {port_name!r}; restart `run` to use {new.port!r}")

    def wake_at():
        due = state["engine"].next_due()
        return poll_at if due is None else min(poll_at, due)

    def on_wake(now):
        nonlocal poll_at
        engine = state["engine"]
        due = engine.next_due()
        if due is not None and now + TICK_SLACK >= due:  # float error can leave `now` a hair early
            send_all(engine.tick(now))
        if now >= poll_at:
            poll_at = now + RELOAD_POLL_SECONDS
            reload()

    guard = Guard(silencer or Silencer(decoder.layout), say, allow_typing)
    code = 0
    previous = signal.signal(signal.SIGTERM, _terminate)
    try:
        if decoder.layout["provisional"]:
            say("# layout is provisional: dials decode as 'enc.?' and send no MIDI yet")
        say(f"# {'dry run, no port opened' if dry_run else 'virtual port ' + repr(port_name)}")
        say(f"# playing {source.path}")
        watch(
            decoder,
            on_report,
            say,
            on_lost=lambda: send_all(state["engine"].release_all()),
            on_pad=guard.on_pad,
            on_tick=guard.tick,
            on_wake=on_wake,
            wake_at=wake_at,
            clock=clock,
        )
    except SilenceError as exc:
        print(refusal_message(exc), file=err, flush=True)
        code = 1
    finally:
        signal.signal(signal.SIGTERM, previous)
        send_all(state["engine"].release_all())
        port.close()
        guard.close()
    return code
