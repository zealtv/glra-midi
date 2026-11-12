"""Read-only: poll the pad's UserKeyMapping every 20 ms, print a timestamped line on each change."""
import subprocess, sys, time, re
M = '{"VendorID":0x36AE,"ProductID":0x2475}'
dur = float(sys.argv[1]) if len(sys.argv) > 1 else 60
def snap():
    out = subprocess.run(["hidutil","property","--matching",M,"--get","UserKeyMapping"],capture_output=True,text=True).stdout
    svcs = {}
    cur = None
    for l in out.splitlines():
        m = re.match(r"^([0-9a-f]+)\s+UserKeyMapping", l)
        if m:
            cur = m.group(1)
            svcs.setdefault(cur, 0)
        elif "MappingSrc" in l: svcs[cur] += 1
    return tuple(sorted(svcs.values())), tuple(sorted(svcs))
last = None; t0 = time.time(); end = t0 + dur
while time.time() < end:
    s = snap()
    if s != last:
        print(f"{time.strftime('%H:%M:%S')}.{int(time.time()*1000)%1000:03d} entries-per-service={s[0]} services={s[1]}", flush=True)
        last = s
    time.sleep(0.02)
print("poll finished", flush=True)
