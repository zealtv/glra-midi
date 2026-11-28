import usb.core, usb.util, usb.backend.libusb1
be = usb.backend.libusb1.get_backend(find_library=lambda x: "/opt/homebrew/lib/libusb-1.0.dylib")
d = usb.core.find(idVendor=0x1189, idProduct=0x8890, backend=be)
print(d)  # cached device + config descriptors (no device I/O beyond enumeration cache)
for i in range(1, 6):
    try: print("string", i, repr(usb.util.get_string(d, i)))
    except Exception as e: print("string", i, "err", e)
# HID report descriptor for each interface: standard GET_DESCRIPTOR(0x22), read-only
for intf in d.get_active_configuration():
    n = intf.bInterfaceNumber
    try:
        rd = d.ctrl_transfer(0x81, 0x06, 0x2200, n, 512)
        print("if", n, "report desc", bytes(rd).hex())
    except Exception as e:
        print("if", n, "report desc err", e)
