Probes run on 2026-11-12, during planning (run from Ghostty; Input Monitoring reported granted).

- `seize.swift` (`swiftc -O seize.swift -o seize && ./seize`): tries
  `kIOHIDOptionsTypeSeizeDevice` on every pad interface and prints the IOReturn
  code. Result: vendor `ff00/02` → 0x0; keyboard interfaces → 0xe00002c1
  (kIOReturnNotPrivileged).
- `seize.py <seconds>` (run with the glra-studio venv python): the same through
  hidapi's `hid_darwin_set_open_exclusive(1)`. Exclusive open failed; with
  the flag set to 0 (non-exclusive), both keyboard interfaces opened. It prints any reports
  that arrive, so it can serve as a first capture tool.
