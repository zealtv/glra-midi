# SPDX-License-Identifier: GPL-3.0-only

"""`glra-osc monitor`: read-only, non-exclusive live view of the pad's controls.

One reader thread per input interface feeds a queue; the main thread decodes
and prints. An unplugged interface ends its thread; the main loop rescans once
a second and reopens whatever is missing. Nothing is ever written to the pad.
"""

import queue
import signal
import sys
import threading
import time

from .decode import Decoder
from .device.backend import enumerate_devices, open_device
from .events import format_event, format_time
from .profile import load_profile
from .silence import Guard, SilenceError, Silencer, TYPING_WARNING, check_interval, refusal_message

INTERFACE_SOURCE = {0: "keys", 1: "consumer"}  # interface 2 is the silent vendor channel
RESCAN_SECONDS = 1.0
# While the pad is absent, scan this often: a replugged pad has no key mapping until `on_pad`
# runs, so a slow scan is itself a leak window. One enumeration took ~1.6 ms (2026-11-12).
FAST_RESCAN_SECONDS = 0.1


def find_sources():
    """Map each input source to the enumerated device info for it."""
    found = {}
    for info in enumerate_devices():
        source = INTERFACE_SOURCE.get(info["interface_number"])
        if source and source not in found:
            found[source] = info
    return found


def render(decoder, source, report, t, wall, raw=False, orientation=None):
    """Lines to print for one report: an optional raw line, then one per event.

    `orientation` (a profile's `[pad] orientation`) labels events with displayed numbers.
    """
    lines = []
    if raw:
        lines.append(f"{format_time(wall)} RAW {source} {bytes(report).hex()}")
    lines += [format_event(e, wall, orientation) for e in decoder.feed(source, report, t)]
    return lines


def _reader(source, info, events, stop):
    """Thread body: queue reports; queue ("lost", ...) and exit on any read/open error."""
    try:
        with open_device(info) as device:
            events.put(("opened", source))
            while not stop.is_set():
                data = device.read(64, 100)
                if data:
                    events.put(("report", source, bytes(data), time.monotonic(), time.time()))
    except (OSError, ValueError, RuntimeError) as exc:
        events.put(("lost", source, str(exc) or type(exc).__name__))
    else:
        events.put(("lost", source, "stopped"))


def _next_event(events, timeout):
    """The next queued item, or None after `timeout` seconds (the loop's only blocking wait)."""
    try:
        return events.get(timeout=timeout)
    except queue.Empty:
        return None


def watch(
    decoder,
    on_report,
    say,
    on_lost=None,
    on_pad=None,
    on_tick=None,
    on_wake=None,
    wake_at=None,
    clock=time.monotonic,
):
    """Read the pad until KeyboardInterrupt; the loop `monitor` and `run` share.

    `on_report(source, data, t, wall)` gets each raw report. When an interface
    drops, the decoder resets and `on_lost()` runs (so `run` can release held
    notes) before the rescan reopens it. `say(text)` prints status lines.
    `on_pad()` runs each time the pad (re)appears with all its input interfaces
    visible, before any reader opens (silent-capture applies its key mapping
    there). If it raises, the loop ends with that exception. `on_tick()` runs
    on `silence.check_interval`'s schedule while the pad is present: every
    FAST_CHECK_SECONDS for FAST_WINDOW_SECONDS after each `on_pad`, then every
    CHECK_SECONDS (silent-capture re-verifies its key mapping there); it should
    not raise. `wake_at()` returns the clock time the caller wants `on_wake(now)` by (or
    None): the loop never sleeps past it, and calls `on_wake(clock())` after every wait, after
    any queued report has been handled, so a pad event never waits on it. `run` drives glide
    ticks and profile reloads from these. `clock` is injectable for tests.
    """
    events = queue.Queue()
    stop = threading.Event()
    threads = {}  # source -> Thread
    waiting_noted = False
    pad_present = False
    connected_at = 0.0  # clock() when on_pad last finished
    scan_error = None  # last enumerate failure reported

    try:
        next_scan = 0.0
        next_tick = 0.0
        while True:
            if clock() >= next_scan:
                next_scan = clock() + (RESCAN_SECONDS if pad_present else FAST_RESCAN_SECONDS)
                missing = [s for s in INTERFACE_SOURCE.values() if s not in threads]
                if missing:
                    try:
                        found = find_sources()
                    except Exception as exc:  # hidapi enumeration trouble: retry next scan
                        found = {}
                        if str(exc) != scan_error:  # fast rescans would repeat it 10x a second
                            say(f"# enumerate failed: {exc}")
                        scan_error = str(exc)
                    else:
                        scan_error = None
                    if on_pad and not pad_present and set(INTERFACE_SOURCE.values()) <= set(found):
                        on_pad()
                        pad_present = True
                        connected_at = clock()
                        next_tick = connected_at + check_interval(0.0)
                    for source in missing:
                        if source in found:
                            t = threading.Thread(
                                target=_reader,
                                args=(source, found[source], events, stop),
                                daemon=True,
                            )
                            threads[source] = t
                            t.start()
                    if not found and not waiting_noted:
                        say("# waiting for the pad (36ae:2475)...")
                        waiting_noted = True
            now = clock()
            if on_tick and pad_present and now >= next_tick:
                on_tick()
                now = clock()
                next_tick = now + check_interval(now - connected_at)
            # Wake for the next scan or tick, whichever comes first (a plain 0.25 s read
            # timeout would cap the fast tick at 4 Hz).
            due = next_scan
            if on_tick and pad_present:
                due = min(due, next_tick)
            if wake_at:
                wake = wake_at()
                if wake is not None:
                    due = min(due, wake)
            item = _next_event(events, min(0.25, max(0.0, due - now)))
            if item is None:
                pass
            elif item[0] == "report":
                _, source, data, t, wall = item
                on_report(source, data, t, wall)
            elif item[0] == "opened":
                waiting_noted = False
                say(f"# {item[1]} interface open")
            else:  # lost
                _, source, why = item
                threads.pop(source, None)
                pad_present = False  # re-run on_pad when the pad is back
                next_scan = min(next_scan, clock() + FAST_RESCAN_SECONDS)  # don't wait out a slow scan
                decoder.reset()
                if on_lost:
                    on_lost()
                waiting_noted = False
                say(f"# {source} interface lost ({why}); retrying")
            if on_wake:
                on_wake(clock())
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        for t in threads.values():
            t.join(timeout=1.0)


def _terminate(signum, frame):
    raise KeyboardInterrupt  # same exit path as Ctrl-C


def run(raw=False, out=None, err=None, allow_typing=False, silencer=None, profile=None):
    """`profile`: a profile file path; its orientation numbers the events (ProfileError propagates)."""
    out, err = out or sys.stdout, err or sys.stderr
    orientation = load_profile(profile).orientation if profile else None
    decoder = Decoder()

    def say(text):
        print(text, file=out, flush=True)

    guard = Guard(silencer or Silencer(decoder.layout), say, allow_typing)

    def on_report(source, data, t, wall):
        for line in render(decoder, source, data, t, wall, raw, orientation):
            say(line)

    if orientation:
        say(f"# {orientation}: numbers are as displayed, physical id in brackets")
    if decoder.layout["provisional"]:
        say("# layout is provisional: all dials decode as 'enc.?' (loom:unique-assignments)")
    if allow_typing:
        print(TYPING_WARNING, file=err, flush=True)
    previous = signal.signal(signal.SIGTERM, _terminate)
    try:
        watch(decoder, on_report, say, on_pad=guard.on_pad, on_tick=guard.tick)
    except SilenceError as exc:
        print(refusal_message(exc), file=err, flush=True)
        return 1
    finally:
        signal.signal(signal.SIGTERM, previous)
        guard.close()
    return 0
