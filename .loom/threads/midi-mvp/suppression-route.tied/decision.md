# Decision (2026-11-12): route 1+2, remappable codes plus a per-device no-op mapping, no root

Evidence (with Bob at the pad, macOS 14.6, from Ghostty, non-root):
- Key 7 was a bent pin, now fixed by Bob. It reports `0x5B` with real press and release
  (`raw-report-capture.tied/captures/5-check.jsonl`).
- `dials.sh`: with consumer `E9→0x700000000`, `EA→0xC00000000`, `E2→0x7000000FF`
  applied device-matched, three right clicks, three left clicks and a push changed neither
  volume nor mute, nothing reached the terminal, **and the non-exclusive hidapi reader
  still received the original `03 ea/e9/e2` reports.**
- Non-root hidutil accepts F13–F24 and `0x46–0x4D`, `0x65`, `0x74`, `0x75`,
  International/LANG, reserved, and consumer `E3–E8`/`F0–F2`. It refuses keypad
  and alphanumeric sources.
- Interface 0's key array allows usages 0–0xFF (descriptor Logical Max 0xFF).

Consequences:
- `unique-assignments`: keys → keyboard codes from the accepted set (F13–F24,
  `0x46–0x49`), which keeps 6KRO for chords; dials → unused consumer codes (`E3–E8`,
  `F0–F2`). The consumer report holds one usage at a time, which is fine for dials but
  not for keys.
- `silent-capture`: apply the mapping on connect and on every replug (replug wipes it),
  and restore Bob's own entry (CapsLock→Cmd, as observed) on exit.
  Verify keyboard-page sources go silent the same way.
- Root seize and Karabiner are no longer needed.
