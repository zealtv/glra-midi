"""Guided raw HID capture for the K16_N3 (non-exclusive, read-only).

Run with any Python that has hidapi, e.g. ../glra-studio/.venv/bin/python.
Usage: capture.py <phase> <out.jsonl>   phase: capture | suppress | replug

Records every input report from every pad interface, every byte typed into
this terminal (pad keystrokes that leak through to the focused app), and the
system output volume around dial steps (consumer-key leakage).
"""

import ctypes
import json
import os
import select
import subprocess
import sys
import termios
import threading
import time
import tty

import hid

VID, PID = 0x36AE, 0x2475
lib = ctypes.CDLL(hid.__file__)
lib.hid_darwin_set_open_exclusive.argtypes = [ctypes.c_int]
lib.hid_darwin_set_open_exclusive(0)  # never seize

DIALS = ["UPPER", "MIDDLE", "LOWER"]
lock = threading.Lock()
state = {"step": "setup", "stop": False}
out = None
t0 = time.monotonic()


def log(**rec):
    rec["t"] = round(time.monotonic() - t0, 4)
    rec["step"] = state["step"]
    with lock:
        out.write(json.dumps(rec) + "\n")
        out.flush()


def key_name(k):
    r, c = (k - 1) // 4 + 1, (k - 1) % 4 + 1
    return f"KEY {k}  (row {r}, column {c}; row 1 = row furthest from you, column 1 = left)"


def steps(phase):
    if phase == "capture":
        yield "baseline", "Hands off the pad.", 3
        for k in range(1, 17):
            yield f"key{k}", f"{key_name(k)}: tap once, then press and HOLD ~1 s, release.", 4
        for i, d in enumerate(DIALS, 1):
            yield f"enc{i}-cw-slow", f"{d} dial: turn RIGHT slowly, 3 clicks.", 4
            yield f"enc{i}-ccw-slow", f"{d} dial: turn LEFT slowly, 3 clicks.", 4
            yield f"enc{i}-cw-fast", f"{d} dial: spin RIGHT fast (about 10 clicks).", 3
            yield f"enc{i}-push", f"{d} dial: press once, then press and HOLD ~1 s.", 4
        yield "combo-keys", "Hold KEY 1, tap KEY 2, then release both.", 4
        yield "combo-key-dial", "Hold KEY 1, turn UPPER dial RIGHT 2 clicks, release.", 4
    elif phase == "suppress":
        yield "baseline", "Hands off the pad.", 2
        for k in range(1, 17):
            yield f"key{k}", f"{key_name(k)}: tap once.", 2.5
        for i, d in enumerate(DIALS, 1):
            yield f"enc{i}-cw", f"{d} dial: turn RIGHT 2 clicks.", 3
            yield f"enc{i}-ccw", f"{d} dial: turn LEFT 2 clicks.", 3
            yield f"enc{i}-push", f"{d} dial: press once.", 3
    elif phase == "dials":
        yield "baseline", "Hands off the pad.", 2
        yield "enc1-cw", "UPPER dial: turn RIGHT 3 clicks, slowly.", 5
        yield "enc1-ccw", "UPPER dial: turn LEFT 3 clicks, slowly.", 5
        yield "enc1-push", "UPPER dial: press once.", 5
    elif phase == "replug":
        yield "after-replug-key1", "KEY 1: tap twice.", 3
        yield "after-replug-enc1", "UPPER dial: turn RIGHT 2 clicks, then press once.", 4


def volume():
    try:
        return subprocess.run(
            ["osascript", "-e", "get volume settings"], capture_output=True, text=True, timeout=3
        ).stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"error {e}"


def reader(path, info):
    while not state["stop"]:
        dev = hid.device()
        try:
            dev.open_path(path)
            log(kind="open", path=path.decode(), **info)
            while not state["stop"]:
                r = dev.read(64, 100)
                if r:
                    h = bytes(r).hex()
                    log(kind="hid", path=path.decode(), hex=h, **info)
                    print(f"\r      <- if{info['iface']} {h}\r", flush=True)
        except (OSError, ValueError) as e:
            log(kind="hid_error", path=path.decode(), error=str(e), **info)
        finally:
            try:
                dev.close()
            except Exception:  # noqa: BLE001
                pass
        time.sleep(0.5)
        return  # path dies with the device; main loop reopens new paths


def tty_reader():
    fd = sys.stdin.fileno()
    while not state["stop"]:
        if select.select([fd], [], [], 0.1)[0]:
            b = os.read(fd, 64)
            log(kind="tty", hex=b.hex(), text=b.decode("latin1"))
            print(f"\r      !! LEAKED to terminal: {b!r}\r", flush=True)


def interfaces():
    by = {}
    for d in hid.enumerate(VID, PID):
        e = by.setdefault(d["path"], {"iface": d["interface_number"], "usages": []})
        e["usages"].append(f"{d['usage_page']:x}/{d['usage']:x}")
    return by


def watcher():
    open_paths = set()
    while not state["stop"]:
        current = interfaces()
        for p, info in current.items():
            if p not in open_paths:
                open_paths.add(p)
                threading.Thread(target=reader, args=(p, info), daemon=True).start()
        gone = open_paths - set(current)
        if gone:
            log(kind="gone", paths=[g.decode() for g in gone])
            open_paths -= gone
        state["present"] = bool(current)
        time.sleep(0.5)


def main():
    global out
    phase, path = sys.argv[1], sys.argv[2]
    out = open(path, "a")
    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    tty.setraw(fd)
    try:
        log(kind="phase", phase=phase, interfaces={k.decode(): v for k, v in interfaces().items()})
        threading.Thread(target=watcher, daemon=True).start()
        threading.Thread(target=tty_reader, daemon=True).start()
        time.sleep(1)
        print(f"\r\n=== {phase.upper()} — follow the prompts; no need to press Enter ===\r\n")
        if phase == "replug":
            state["step"] = "unplug"
            print("\r\n>>> UNPLUG the pad now, wait 2 s, then plug it back in.\r\n", flush=True)
            deadline = time.monotonic() + 60
            while state.get("present", True) and time.monotonic() < deadline:
                time.sleep(0.2)
            log(kind="unplugged", ok=not state.get("present", True))
            while not state.get("present") and time.monotonic() < deadline:
                time.sleep(0.2)
            log(kind="replugged", ok=bool(state.get("present")))
            time.sleep(3)
            m = subprocess.run(
                ["hidutil", "property", "--matching",
                 '{"VendorID":0x36ae,"ProductID":0x2475}', "--get", "UserKeyMapping"],
                capture_output=True, text=True,
            ).stdout
            log(kind="mapping_after_replug", text=m)
        for i, (name, prompt, secs) in enumerate(steps(phase)):
            dial = name.startswith("enc") or "dial" in name
            if dial:
                log(kind="volume_before", value=volume())
            state["step"] = name
            print(f"\r\n>>> {prompt}\r\n", flush=True)
            end = time.monotonic() + secs
            while time.monotonic() < end:
                left = end - time.monotonic()
                print(f"\r    {'#' * int(left * 4):<24}", end="", flush=True)
                time.sleep(0.1)
            state["step"] = f"{name}-tail"
            time.sleep(0.4)  # let trailing releases land in the same step
            if dial:
                log(kind="volume_after", value=volume())
        state["step"] = "done"
        print("\r\n=== phase done ===\r\n", flush=True)
    finally:
        state["stop"] = True
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)
        time.sleep(0.3)
        out.close()


if __name__ == "__main__":
    main()
