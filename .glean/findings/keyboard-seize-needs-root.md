# Seizing the pad's keyboard interfaces failed without root, so suppression needs another route or root

When trying to stop the pad typing into apps, or seeing 0xe00002c1 / "open failed" on an exclusive open.

## Triggers
- seize
- kIOHIDOptionsTypeSeizeDevice
- 0xe00002c1
- kIOReturnNotPrivileged
- hidutil
- UserKeyMapping
- Input Monitoring

## Context
Probes on 2026-11-12 from Ghostty (macOS 14.6, arm64), not as root
(scripts: `.loom/threads/midi-mvp/raw-report-capture/spike/`):
- `IOHIDCheckAccess(ListenEvent)` returned granted.
- Seize on both keyboard interfaces → `0xe00002c1` (kIOReturnNotPrivileged);
  seize on the vendor interface → success. hidapi's exclusive open failed the
  same way; its non-exclusive open of the keyboard interfaces succeeded.
- `sudo -n` needs a password, so agents can't test the root route unattended.
- `hidutil property --matching '{"VendorID":0x36ae,"ProductID":0x2475}'`
  works without root and showed a CapsLock→Cmd `UserKeyMapping` already on the
  pad's services (presumably Bob's global remap).

Web research the same day (`.loom/threads/midi-mvp/suppression-route/research.md`)
found no non-root seize route. Karabiner seizes from a root process. Reports
suggest keyboard input-report callbacks don't fire without Input Monitoring,
and that `IOHIDCheckAccess` can misreport, so the "granted" above is weak evidence.
Root daemons may need their own TCC grant.

Candidate routes and the decision belong to `loom:suppression-route`;
revise this finding with the outcome.

## Associations
- [[k16n3-hid-interfaces]]
- [[brief-is-direction]]
