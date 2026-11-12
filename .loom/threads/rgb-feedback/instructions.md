# rgb-feedback — host-driven pad lighting (sketch)

Sketch only. Split when picked up.

Start from glra-studio's `lighting.py`: global Off/Steady/Breathing/Rainbow
plus steady RGB, tested on this firmware. Unknowns: per-key LEDs (the
`parsaj-dev/sdcx-keypad` project documents some for another model), whether
writes wear flash (glra-studio does careful backup/readback per write; that's too
slow and risky for live feedback), latency. Go carefully: don't write at high
frequency until the storage behaviour is understood. Brief §7.
