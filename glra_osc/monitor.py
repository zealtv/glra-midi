# SPDX-License-Identifier: GPL-3.0-only

"""`glra-osc monitor`: read-only, non-exclusive live view of the pad's controls.

One reader thread per input interface feeds a queue; the main thread decodes
and prints. An unplugged interface ends its thread; the main loop rescans once
a second and reopens whatever is missing. Nothing is ever written to the pad.
"""

import queue
import sys
import threading
import time

from .decode import Decoder
from .device.backend import enumerate_devices, open_device
from .events import format_event, format_time

INTERFACE_SOURCE = {0: "keys", 1: "consumer"}  # interface 2 is the silent vendor channel
RESCAN_SECONDS = 1.0


def find_sources():
    """Map each input source to the enumerated device info for it."""
    found = {}
    for info in enumerate_devices():
        source = INTERFACE_SOURCE.get(info["interface_number"])
        if source and source not in found:
            found[source] = info
    return found


def render(decoder, source, report, t, wall, raw=False):
    """Lines to print for one report: an optional raw line, then one per event."""
    lines = []
    if raw:
        lines.append(f"{format_time(wall)} RAW {source} {bytes(report).hex()}")
    lines += [format_event(e, wall) for e in decoder.feed(source, report, t)]
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


def watch(decoder, on_report, say, on_lost=None):
    """Read the pad until KeyboardInterrupt; the loop `monitor` and `run` share.

    `on_report(source, data, t, wall)` gets each raw report. When an interface
    drops, the decoder resets and `on_lost()` runs (so `run` can release held
    notes) before the rescan reopens it. `say(text)` prints status lines.
    """
    events = queue.Queue()
    stop = threading.Event()
    threads = {}  # source -> Thread
    waiting_noted = False

    try:
        next_scan = 0.0
        while True:
            if time.monotonic() >= next_scan:
                next_scan = time.monotonic() + RESCAN_SECONDS
                missing = [s for s in INTERFACE_SOURCE.values() if s not in threads]
                if missing:
                    try:
                        found = find_sources()
                    except Exception as exc:  # hidapi enumeration trouble: retry next scan
                        found = {}
                        say(f"# enumerate failed: {exc}")
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
            try:
                item = events.get(timeout=0.25)
            except queue.Empty:
                continue
            if item[0] == "report":
                _, source, data, t, wall = item
                on_report(source, data, t, wall)
            elif item[0] == "opened":
                waiting_noted = False
                say(f"# {item[1]} interface open")
            else:  # lost
                _, source, why = item
                threads.pop(source, None)
                decoder.reset()
                if on_lost:
                    on_lost()
                waiting_noted = False
                say(f"# {source} interface lost ({why}); retrying")
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        for t in threads.values():
            t.join(timeout=1.0)


def run(raw=False, out=None):
    out = out or sys.stdout
    decoder = Decoder()

    def say(text):
        print(text, file=out, flush=True)

    def on_report(source, data, t, wall):
        for line in render(decoder, source, data, t, wall, raw):
            say(line)

    if decoder.layout["provisional"]:
        say("# layout is provisional: all dials decode as 'enc.?' (loom:unique-assignments)")
    watch(decoder, on_report, say)
    return 0
