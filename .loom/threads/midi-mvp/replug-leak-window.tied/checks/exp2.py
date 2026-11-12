"""Wait for the pad to re-enumerate, apply our mapping once 2 s later, hold 10 s, remove ours."""
import subprocess, time, re, sys
sys.path.insert(0, "/Users/bob/repos/glra-osc")
from glra_osc.decode import Decoder
from glra_osc.silence import Silencer
M = '{"VendorID":0x36AE,"ProductID":0x2475}'
def ids():
    out = subprocess.run(["hidutil","property","--matching",M,"--get","UserKeyMapping"],capture_output=True,text=True).stdout
    return set(re.findall(r"^([0-9a-f]+)\s+UserKeyMapping", out, re.M))
def ts(): return time.strftime('%H:%M:%S') + f".{int(time.time()*1000)%1000:03d}"
before = ids(); print(ts(), "waiting; current services", sorted(before), flush=True)
while True:
    now = ids()
    if len(now) == 2 and now != before and not (now & before): break
    if not now: before = set()
    time.sleep(0.02)
print(ts(), "pad appeared", sorted(now), flush=True)
time.sleep(2.0)
s = Silencer(Decoder().layout)
print(ts(), "apply ->", s.apply(), "services", flush=True)
time.sleep(10.0)
print(ts(), "restore ->", s.restore(), flush=True)
