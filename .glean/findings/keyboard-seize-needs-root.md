# Seizing the pad's keyboard interfaces failed without root; a no-root hidutil remap works only for non-alphanumeric codes

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

Hands-on tests, 2026-11-12, macOS 14.6, non-root:
- `hidutil ... --set UserKeyMapping` **refuses the whole set** if any source
  is alphanumeric/keypad: "Run as root to remap alphanumerics / special
  characters with UserKeyMapping". So the stock numpad codes can't be remapped.
- Accepted without root: F13–F24 (`0x68–0x73`), International1–9
  (`0x87–0x8F`), LANG1–9 (`0x90–0x98`), `0x7E`, `0xE8`, consumer usages.
  A 30-entry set of these applied to both pad services.
- Replug wipes the per-device mapping, so it has to be reapplied on every connect.
- Untested: whether the destination truly emits nothing, and whether the raw hidapi
  reader still sees the original usage under the mapping.

Candidate routes and the decision belong to `loom:suppression-route`;
revise this finding with the outcome.

## Associations
- [[k16n3-hid-interfaces]]
- [[brief-is-direction]]
