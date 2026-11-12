"""Program the K16_N3 with 25 unique, remappable assignments (2026-11-12).

Dry run by default; `--apply` writes. Every write goes through the vendored
glra-studio `write_one`: fresh backup, then write, then a full readback that
must differ only in that slot. Restore with `--restore <full-backup.json>`.

Run from the repo root:  .venv/bin/python <this file> [--apply | --restore F]
"""

import json
import sys
from pathlib import Path

from glra_osc.device import backend, storage, transactions
from glra_osc.device.protocol import Reader

HERE = Path(__file__).resolve().parent

# Bob's pad reports firmware 103 / internal PID 0x2475; glra-studio only tested
# writes on 100 / 0x246D. On 2026-11-12 Bob approved a one-slot trial on 103. Allow
# exactly that fingerprint here; the vendored module stays unchanged.
BOB_PAD = (1, 0x2475, 103, 6, 1)
_validate = transactions.validate_status


def _validate_bob(status):
    if transactions.fingerprint(status) == BOB_PAD:
        if status["current_profile"] != 0 or status["current_layer"] != 0:
            raise ValueError("Unexpected profile/layer")
        return
    _validate(status)


transactions.validate_status = _validate_bob
ROWS = [[0, 1, 2, 3], [7, 8, 9, 10], [14, 15, 16, 17], [21, 22, 23, 24]]  # glra-studio rows
DIAL_SLOTS = [(4, 5, 6), (11, 12, 13), (18, 19, 20)]  # (push, glra "cw", glra "ccw")


def key_slot(k):
    """Bob's key k (row 1 = far edge, by the dials) -> glra slot. Verified 2026-11-12."""
    r, c = (k - 1) // 4 + 1, (k - 1) % 4 + 1
    return ROWS[c - 1][4 - r]


# Revised 2026-11-12 after the DAW check: macOS turned F14/F15 (keys 2, 3) and
# PrintScreen/ScrollLock (keys 13, 14) into brightness. Those keys now use Home/PageUp/End/PageDown.
KEY_USAGES = [0x68, 0x4A, 0x4B] + list(range(0x6B, 0x74)) + [0x4D, 0x4E, 0x48, 0x49]
DIAL_USAGES = [(0xE3, 0xE4, 0xE5), (0xE6, 0xE7, 0xE8), (0xF0, 0xF1, 0xF2)]


def plan():
    rows = []
    for k, u in enumerate(KEY_USAGES, 1):
        rows.append((key_slot(k), f"key.{k}", f"20 00 {u:02x} 00", "assignment"))
    for d, (slots, usages) in enumerate(zip(DIAL_SLOTS, DIAL_USAGES), 1):
        for part, slot, u in zip(("push", "a", "b"), slots, usages):
            # Consumer values have the stock shape `30 uu 00 00`. glra-studio's recorder only
            # allows keyboard values, so these go through its verified "restore" path.
            rows.append((slot, f"enc.{d}.{part}", f"30 {u:02x} 00 00", "restore"))
    assert len({r[0] for r in rows}) == 25 and len({r[2] for r in rows}) == 25
    return rows


def main():
    apply = "--apply" in sys.argv
    restore = sys.argv[sys.argv.index("--restore") + 1] if "--restore" in sys.argv else None
    tx_dir = HERE / "transactions"
    tx_dir.mkdir(exist_ok=True)
    audit = storage.Audit(tx_dir / "logs")
    info = backend.select()
    with backend.open_device(info) as dev:
        reader = Reader(dev, audit)
        status, tables = transactions.snapshot(reader)
        current = bytes.fromhex(tables["0"])
        if restore:
            src = bytes.fromhex(json.loads(Path(restore).read_text())["assignments"]["0"])
            rows = [(s, f"slot {s}", src[s * 4 : s * 4 + 4].hex(" "), "restore")
                    for s in sorted({x for r in ROWS for x in r} | {x for g in DIAL_SLOTS for x in g})]
        else:
            rows = plan()
            if "--only" in sys.argv:
                only = sys.argv[sys.argv.index("--only") + 1].split(",")
                rows = [r for r in rows if r[1] in only]
            full = HERE / "pre-write-backup.json"
            if apply and not full.exists():
                storage.save(full, {"schema": "glra-osc-pre-write-v1", "created": storage.now(),
                                    "device": info, "status": status, "assignments": tables})
                print(f"full backup: {full}")
        for slot, name, value, purpose in rows:
            old = current[slot * 4 : slot * 4 + 4].hex()
            new = value.replace(" ", "")
            flag = "same" if old == new else ("WRITE" if apply else "would write")
            print(f"slot {slot:2d} {name:<12} {old} -> {new}  {flag}")
            if apply and old != new:
                transactions.write_one(reader, info, slot, new, old, tx_dir, purpose)
                print("           verified")
    audit.close()


if __name__ == "__main__":
    main()
