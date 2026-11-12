# The pad is silenced without root by a per-device hidutil mapping to "no event"; seizing needs root and isn't used

When trying to stop the pad typing into apps, editing `glra_osc/silence.py`, or seeing 0xe00002c1 / "open failed" on an exclusive open, or "Run as root to remap alphanumerics".

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

## Outcome (2026-11-12)
`loom:suppression-route` chose the hidutil route; `loom:silent-capture` built it in
`glra_osc/silence.py`. `glra-osc run` and `monitor` map every layout code (25) to
`0x700000000` through `hidutil property --matching {VendorID,ProductID} --set`, merged
with the entries already on the pad's services (Bob's CapsLock→Cmd), verified by
re-reading. They re-apply on every (re)connect from `watch(on_pad=...)`, re-verify every 100 ms for 10 s after each
connect, then every 2 s (`on_tick`, `silence.check_interval`) and re-merge ours if macOS replaced the mapping, remove only our sources
from the *current* mapping on exit/Ctrl-C/SIGTERM, and refuse to run without `--allow-typing`
if apply or verify fails. A refusal prints the "Run as root" text to stdout with exit 1
and applies nothing. After `kill -9` the mapping stays until replug;
`glra-osc unsilence` removes entries whose source is ours, and a later run treats
such leftovers as "not original". With no mapping, `--get` prints each service
with an empty `( )`; with no matching service it prints nothing. The raw hidapi
readers still see the original reports under the mapping.

Revision, 2026-11-12 (Bob's live DAW test): after a replug macOS reapplied
CapsLock→Cmd a moment after we applied ours, replacing the whole mapping (pad keys
leaked), and a connect-time "original" snapshot then restored 0 entries, losing
CapsLock. So never restore a snapshot: macOS can rewrite the mapping at any time.

Revision, 2026-11-12 (replug-leak-window): a 2 s re-check still let one key (Home) type after a replug, so
the first 10 s after each connect re-check every 100 ms (one `hidutil --get` takes about 5 ms). The real
connect-to-overwrite delay has not been measured yet (no replug happened); Bob's replug test is pending.

## Associations
- [[k16n3-hid-interfaces]]
- [[brief-is-direction]]
