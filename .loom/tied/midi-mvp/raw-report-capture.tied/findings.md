# Raw report capture: findings (2026-11-12)

The session ran with Bob at the pad, using the stock assignments, a non-exclusive hidapi
reader on all three interfaces, and the focused tmux pane catching keystrokes that leaked.
Tools: `capture.py` (guided timed prompts), `session.sh` (the whole run),
`dials.sh` (consumer-mapping test), `analyze.py` (per-step summary).
Raw logs are in `captures/`. Bob said the prompts ran fast and some of his
input was rough, so treat the timing below as indicative. The report structure itself
is unambiguous.

## Reports
- **Keys → interface 0** (boot keyboard, page 1/usage 6). 8-byte reports:
  `mod, 00, k1..k6` (6KRO). Each press sends one report with the usage, and each release
  sends a report with that usage removed. **Releases are real:** hold times of
  0.4–1.3 s showed up as the gap between the two reports. Two keys held together
  showed as `00 00 56 57 …`. The device sends no auto-repeat (the repeat seen in the
  terminal comes from macOS).
- **Dials → interface 1, report ID 3, consumer page**, 3-byte report
  `03 <usage lo> <usage hi>`. Release = `03 00 00`.
  - Turns: each detent = press plus release **1–2 ms apart**. Fast spins delivered
    detents 10–30 ms apart, and none merged in what was captured.
  - Push: press → release when the button is let go (130–580 ms observed),
    so **push releases are real**.
  - Turning while pushed: one capture shows the push usage replaced by the
    turn usage with no release in between. That input was rough, so recheck it.
- Interface 1 never carried keyboard usages, and interface 0 never carried consumer.
- **Vendor interface (2): silent** during normal use.
- A key held while turning a dial produced independent reports on both interfaces.

## Bob's physical numbering vs glra-studio slots
Prompts named KEY k as row ⌈k/4⌉ / column, with "row 1 furthest from you".
Bob's presses gave these usages:

| Bob key | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| usage | 56 | 57 | 54 | 58 | 61 | 5e | — | 63 | 60 | 5d | 5a | 62 | 5f | 5c | 59 | 55 |

Against glra-studio's slot table, Bob's row r / column c = glra row c / column 5−r.
So Bob seems to hold the pad with the dials along the far edge, rotated relative to
glra-studio's diagram. In that orientation, the prompts' "UPPER / MIDDLE /
LOWER dial" names are ambiguous, and "turn RIGHT" produced `0xEA` (vol−),
which glra-studio labels counterclockwise. **Settle naming and direction with Bob
during `unique-assignments`** (once each action has its own code, a single press per
control fixes the map).

## Key 7 (Bob's row 2, column 3; expected usage 0x5B "keypad 3")
It produced **no report in either pass**. Bob tapped it again later, between runs,
when no reader was open, so that result is unknown. It could be a dead switch or two missed prompts.
Check it first at the next session.

## Suppression evidence
- Non-root `hidutil` **refuses** any UserKeyMapping set that contains
  alphanumeric/keypad sources: `Run as root to remap alphanumerics / special
  characters with UserKeyMapping`. The whole set is rejected, nothing applies, and so
  the planned row-by-row no-op test never ran.
- Probing single sources (non-root, accepted = applied to both pad services):
  keypad `0x59` refused; F13 `0x68`, F24 `0x73`, `0x7E`, International1 `0x87`,
  reserved `0xE8`, consumer `0xE2`, consumer `0xCD` **accepted**.
- Consumer→{`0xC00000000`, `0x700000000`, `0x7000000FF`} mappings applied
  without root, but Bob had left, so whether they silence the dials, and whether
  the raw reader still sees the original usages, remains **untested**.
  `dials.sh` reruns that test in about 20 seconds.
- **Replug resets** the per-device mapping. After replug the pad carried only
  macOS's own CapsLock→Cmd entry, so the runtime has to reapply on every connect.
- With no mapping, stock dial turns changed system volume and push toggled
  mute (detected via `osascript`), and every key leaked into the terminal.

## Input Monitoring
Reports arrived from Ghostty with no new permission prompt. Whatever
Ghostty already holds is enough for non-exclusive reads.
