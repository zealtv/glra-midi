import ctypes, hid, sys, time
lib = ctypes.CDLL(hid.__file__)
lib.hid_darwin_set_open_exclusive.argtypes=[ctypes.c_int]
lib.hid_darwin_set_open_exclusive(1)
print("exclusive flag", lib.hid_darwin_get_open_exclusive())
paths = sorted({d['path'] for d in hid.enumerate(0x36ae,0x2475) if d['usage_page']!=0xff00})
devs=[]
for p in paths:
    d=hid.device()
    try:
        d.open_path(p); d.set_nonblocking(1); devs.append((p,d)); print("seized", p)
    except Exception as e:
        print("FAILED", p, e)
t=time.time()
while time.time()-t < float(sys.argv[1]):
    for p,d in devs:
        r=d.read(64)
        if r: print(f"{time.time()-t:7.3f}", p.decode(), bytes(r).hex())
    time.sleep(0.002)
for p,d in devs: d.close()
print("released")
