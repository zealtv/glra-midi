import IOKit.hid
import Foundation
let m = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(kIOHIDOptionsTypeNone))
IOHIDManagerSetDeviceMatching(m, [kIOHIDVendorIDKey: 0x36ae, kIOHIDProductIDKey: 0x2475] as CFDictionary)
let set = IOHIDManagerCopyDevices(m) as? Set<IOHIDDevice> ?? []
print("access:", IOHIDCheckAccess(kIOHIDRequestTypeListenEvent).rawValue, "(0 granted,1 denied,2 unknown)")
for d in set {
  let up = IOHIDDeviceGetProperty(d, kIOHIDPrimaryUsagePageKey as CFString) as? Int ?? -1
  let u = IOHIDDeviceGetProperty(d, kIOHIDPrimaryUsageKey as CFString) as? Int ?? -1
  let r = IOHIDDeviceOpen(d, IOOptionBits(kIOHIDOptionsTypeSeizeDevice))
  print(String(format:"page %x usage %x seize -> 0x%08x", up, u, r))
  if r == kIOReturnSuccess { IOHIDDeviceClose(d, IOOptionBits(kIOHIDOptionsTypeNone)) }
}
