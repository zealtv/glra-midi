"""led-probe: guarded lighting probe for Bob's K16_N3 (2026-11-13).

Every write is a dry run unless `--send` is given: the exact packet prints
first so Bob can OK it. Writes allowed here, and nothing else:
  06 0b  global light state (modes 0-12 only, rest copied from the baseline)
  06 14  one key's colour, only at the 16 key slots
  06 16  read firmware defaults for a mode (outside the vendored allowlist)
After every write: ack frames + timing, then `06 0a` and the full `06 13`
read, checking bytes 84+ (the keymap mirror) still equal the baseline.

Run from the repo root:  .venv/bin/python <this file> <command> [...]
  backup                 take the baseline (once; refuses to overwrite)
  read                   light state + colour table vs baseline
  defaults MODE [--send] 06 16 read of a mode's default block
  mode MODE [--send]     06 0b with the baseline payload, mode byte changed
  light HEX11 [--send]   06 0b with an explicit 11-byte payload
  key SLOT RRGGBB [--send]   06 14 one key slot
  restore [--send]       baseline light payload + baseline colours, verified twice
"""

import sys
import time
from pathlib import Path

from glra_osc.device import backend, storage
from glra_osc.device.protocol import Reader

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / "led-probe.tied" / "baseline.json"  # same pad baseline, 2026-11-13
KEY_SLOTS = (0, 1, 2, 3, 7, 8, 9, 10, 14, 15, 16, 17, 21, 22, 23, 24)
ROWS = [[0, 1, 2, 3], [7, 8, 9, 10], [14, 15, 16, 17], [21, 22, 23, 24]]
COLOUR_BYTES = 84  # 28 triples; bytes 84+ of the 06 13 read mirror the keymap


def key_slot(k):
    """Bob's key k -> slot (from loom:unique-assignments, verified for assignments)."""
    r, c = (k - 1) // 4 + 1, (k - 1) % 4 + 1
    return ROWS[c - 1][4 - r]


SLOT_KEY = {key_slot(k): k for k in range(1, 17)}


def packet(*body):
    p = bytearray(65)  # hidapi report ID 0 + 64 bytes
    p[1 : 1 + len(body)] = bytes(body)
    return bytes(p)


def light_packet(payload):
    if len(payload) != 11 or payload[0:2] != b"\x01\x00" or not 0 <= payload[2] <= 12:
        raise ValueError(f"refusing light payload {payload.hex()}")
    return packet(0x06, 0x0B, 0x0B, 0x00, 0x00, *payload)


def key_packet(slot, rgb):
    if slot not in KEY_SLOTS or len(rgb) != 3:
        raise ValueError(f"refusing slot {slot}: only key slots {KEY_SLOTS}")
    off = 3 * slot
    assert off + 3 <= COLOUR_BYTES
    return packet(0x06, 0x14, 0x03, off & 255, off >> 8, 0, 0, 0, *rgb)


def defaults_packet(mode):
    if not 0 <= mode <= 12:
        raise ValueError("mode out of range")
    return packet(0x06, 0x16, 0, 0, 0, 0x01, 0, mode)


def show(p):
    return " ".join(f"{b:02x}" for b in p[1:17]) + "  (zeros to 64)"


def load_baseline():
    if not BASELINE.exists():
        sys.exit("no baseline: run `backup` first")
    return storage.load(BASELINE)


def snapshot(reader):
    light = reader.query(10)[5:16]
    rgb = reader.memory(19, 432)
    return light, rgb


def describe(rgb):
    rows = []
    for k in range(1, 17):
        s = key_slot(k)
        rows.append(f"key {k:2d} (slot {s:2d}) {rgb[3 * s : 3 * s + 3].hex()}")
    others = [s for s in range(28) if s not in KEY_SLOTS and any(rgb[3 * s : 3 * s + 3])]
    if others:
        rows.append(f"NON-KEY SLOTS NONZERO: {others}")
    return "\n".join(rows)


def check(reader, base, label):
    light, rgb = snapshot(reader)
    light2, rgb2 = snapshot(reader)
    stable = light == light2 and rgb == rgb2
    keymap_ok = rgb[COLOUR_BYTES:] == bytes.fromhex(base["rgb"])[COLOUR_BYTES:]
    print(f"[{label}] light {light.hex()}  double-read stable: {stable}  keymap mirror unchanged: {keymap_ok}")
    changed = [
        s for s in range(28) if rgb[3 * s : 3 * s + 3] != bytes.fromhex(base["rgb"])[3 * s : 3 * s + 3]
    ]
    print(f"[{label}] colour slots differing from baseline: {changed}")
    if not keymap_ok or not stable:
        raise RuntimeError("STOP: keymap mirror changed or reads unstable; ask Bob before anything else")
    return light, rgb


def send(reader, p, expect_op):
    dev = reader.device
    for _ in range(32):
        stale = bytes(dev.read(64, 1))
        if not stale:
            break
        reader.audit.record("input_stale", hex=stale.hex())
    reader.audit.record("probe_write", hex=p.hex())
    t0 = time.perf_counter()
    n = dev.write(p)
    frames, t_ack = [], None
    deadline = t0 + 0.5
    while time.perf_counter() < deadline:
        r = bytes(dev.read(64, 20))
        if r:
            t = (time.perf_counter() - t0) * 1000
            frames.append((t, r))
            reader.audit.record("probe_input", hex=r.hex(), ms=t)
            if t_ack is None and r[:2] == bytes([0xAA, expect_op]):
                t_ack = t
    print(f"wrote {n} bytes; frames in 500 ms: {len(frames)}; matching ack at: "
          f"{'none' if t_ack is None else f'{t_ack:.2f} ms'}")
    for t, r in frames:
        print(f"  +{t:7.2f} ms  {r[:24].hex(' ')} ...")
    if n != len(p):
        raise IOError("short write")
    return frames, t_ack


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    cmd, go = args[0], "--send" in args
    args = [a for a in args[1:] if a != "--send"]
    audit = storage.Audit(HERE / "logs")
    info = backend.select()
    with backend.open_device(info) as dev:
        reader = Reader(dev, audit)
        status = reader.status()
        if (status["firmware"], status["internal_pid"]) != (103, 0x2475):
            sys.exit(f"unexpected device {status}")

        if cmd == "backup":
            sys.exit("baseline lives in led-probe.tied")
            if BASELINE.exists():
                sys.exit(f"baseline exists: {BASELINE}")
            data = reader.backup()
            light, rgb = snapshot(reader)
            data.update(device=info, rgb=rgb.hex(), light=light.hex(), taken=storage.now())
            storage.save(BASELINE, data)
            print(f"baseline saved: {BASELINE}\nlight {light.hex()}\n{describe(rgb)}")
            return

        base = load_baseline()
        if cmd == "read":
            light, rgb = check(reader, base, "read")
            print(describe(rgb))
            return

        if cmd == "defaults":
            p, op = defaults_packet(int(args[0])), 0x16
        elif cmd == "mode":
            payload = bytearray(bytes.fromhex(base["light"]))
            payload[2] = int(args[0])
            p, op = light_packet(bytes(payload)), 0x0B
        elif cmd == "light":
            p, op = light_packet(bytes.fromhex(args[0])), 0x0B
        elif cmd == "key":
            p, op = key_packet(int(args[0]), bytes.fromhex(args[1])), 0x14
        elif cmd == "restore":
            return restore(reader, base, go)
        else:
            sys.exit(f"unknown command {cmd}")

        print(f"packet: {show(p)}")
        if cmd == "key":
            print(f"  slot {args[0]} = Bob's key {SLOT_KEY[int(args[0])]}")
        if not go:
            print("dry run; add --send once Bob has OK'd this packet")
            return
        check(reader, base, "before")
        try:
            frames, _ = send(reader, p, op)
            check(reader, base, "after")
        except Exception:
            print("ERROR: running restore")
            restore(reader, base, True)
            raise
    audit.close()


def restore(reader, base, go):
    light0, rgb0 = bytes.fromhex(base["light"]), bytes.fromhex(base["rgb"])
    light, rgb = snapshot(reader)
    plan = []
    if light != light0:
        plan.append((light_packet(light0), 0x0B))
    for s in range(28):
        if rgb[3 * s : 3 * s + 3] != rgb0[3 * s : 3 * s + 3]:
            if s not in KEY_SLOTS:
                raise RuntimeError(f"STOP: non-key slot {s} changed; ask Bob")
            plan.append((key_packet(s, rgb0[3 * s : 3 * s + 3]), 0x14))
    if not plan:
        print("already at baseline")
        check(reader, base, "restore")
        return
    for p, _ in plan:
        print(f"restore packet: {show(p)}")
    if not go:
        print("dry run; add --send to restore")
        return
    for p, op in plan:
        send(reader, p, op)
    light, rgb = check(reader, base, "restored")
    if light != light0 or rgb != rgb0:
        raise RuntimeError("restore did not reach baseline")
    print("restored and verified (two reads)")


if __name__ == "__main__":
    main()
