# suppression-route — choose how the pad stops typing

**Needs Bob at the pad.** Suggested model: Opus.

The pad must produce no keystrokes or media actions in apps while captured.
Other keyboards must keep working. Never fall back silently to "pad still
types". Observed 2026-11-12 (`glean:keyboard-seize-needs-root`):
`IOHIDDeviceOpen(..., kIOHIDOptionsTypeSeizeDevice)` on the keyboard
interfaces returns `kIOReturnNotPrivileged` (0xe00002c1) for a non-root
process; the vendor interface seizes fine; sudo needs a password.

Candidate routes, roughly in Bob's preferred order (least friction / fewest
permissions first). Test the cheap ones by hand before writing code:
1. **Device-matched `hidutil` UserKeyMapping** (no root): remap every usage
   the pad emits to a no-op usage, for VID 36ae / PID 2475 only, and keep
   reading raw reports non-exclusively. Check: what destination truly emits
   nothing; whether the raw reader still sees original usages; consumer-page
   usages; that it resets on replug, so the runtime must reapply and clear it on exit.
   Note the pad already shows a CapsLock→Cmd UserKeyMapping inherited from
   Bob's global setting. Don't clobber his global mapping.
2. **Inert assignments**: program usages macOS ignores (e.g. unassigned
   consumer usages, or keyboard usages with no default action) so the pad is
   silent by construction. Verify in a text field, Finder, a DAW and with
   modifiers held.
3. **Root seize** (sudo or a root launchd daemon). Proven API, but more
   friction. Fallback only.
4. Karabiner-Elements. Last resort.

Web research from 2026-11-12 (Sonnet; claims labelled documented/reported/
inferred) is in `research.md` beside this file. Headlines: no non-root seize
route found; no *documented* no-op UserKeyMapping destination, though one user
reports `0x70000007E` swallowing keys; whether a non-exclusive reader still
sees raw reports under a mapping is untested; there's no source on consumer-page
(0x0C) mappings; reading keyboard reports likely needs Input Monitoring for
whichever binary opens the device.
Decide, record the decision and evidence as a glean finding, and update
`unique-assignments` and `silent-capture` if the choice changes them.
