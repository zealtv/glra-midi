# rgb-feedback — host-driven pad lighting: per-key colour and animations

Goal (Bob, 2026-11-12): set each key's LED individually (one per key), and
run animations both across the whole pad and on single keys. Two consumers:
`midi-feedback` (LED state shows toggles / incoming MIDI) and `banks` (show
which bank is active). Brief §7 (`lore:2026-11-12-initial-brief`).

Known as of 2026-11-12 (`../glra-studio/docs/protocol.md`, firmware 100; Bob's
pad runs 103): only *global* lighting is tested: write `06 0b`, 11-byte
payload (mode Off/Steady/Breathing/Rainbow, brightness, speed, HSV), read `06 0a`.
There is a 432-byte "RGB memory" read with `06 13` (window 19) that no one has
decoded, and no known write for it. glra-studio guards every lighting write with
a backup and readback, which is far too slow for live feedback.

Unknown: whether the K16_N3 has addressable per-key LEDs; whether any per-key or
"direct" command exists; whether writes go to flash (wear) or RAM; the write rate
and latency; whether vendor-interface writes disturb input capture (interfaces 0/1).

Route: research (desk) → probe (hardware, Bob) → choose route with Bob →
driver + animator → demo → acceptance. If only flash-backed or global control
exists, `led-route` rescopes the goal with Bob rather than forcing it.

Device safety (brief §9) applies to every hardware step: back up first, no
firmware/bootloader/reset commands, no writes to unknown memory without Bob's
OK for that specific command, keep a restore path, and don't write at high rate
until storage behaviour is known.
