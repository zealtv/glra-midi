"""Summarise capture JSONL files per step: reports per interface, leaks, volume."""

import collections
import json
import sys

for path in sys.argv[1:]:
    print(f"\n##### {path}")
    steps = collections.OrderedDict()
    for line in open(path):
        r = json.loads(line)
        step = r["step"].removesuffix("-tail")
        s = steps.setdefault(step, {"hid": [], "tty": [], "vol": [], "other": []})
        k = r["kind"]
        if k == "hid":
            s["hid"].append((r["t"], r["iface"], r["hex"].rstrip("0") or "0"))
        elif k == "tty":
            s["tty"].append(r["text"])
        elif k.startswith("volume"):
            s["vol"].append(r["value"].split(",")[0].split(":")[1] + "/" + r["value"].split(":")[-1])
        elif k in ("phase", "open"):
            continue
        else:
            s["other"].append({x: r[x] for x in r if x not in ("t", "step")})
    for step, s in steps.items():
        print(f"\n[{step}]")
        t_prev = None
        for t, iface, h in s["hid"]:
            dt = "" if t_prev is None else f"+{(t - t_prev) * 1000:.0f}ms"
            print(f"  if{iface} {h:<24} {dt}")
            t_prev = t
        if s["tty"]:
            print(f"  LEAKED tty: {''.join(s['tty'])!r}")
        if s["vol"]:
            print(f"  volume before/after: {s['vol']}")
        for o in s["other"]:
            print(f"  {o}")
