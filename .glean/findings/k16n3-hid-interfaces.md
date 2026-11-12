# The K16_N3 shows three HID interfaces, and its stock encoders send duplicate codes

When decoding pad input, picking which interface to open, or reasoning about which control was pressed.

## Triggers
- 36ae
- 2475
- k16_n3
- DevSrvsID
- ff00

## Context
Observed on Bob's pad on 2026-11-12 (USB 36ae:2475, bcdDevice 0x0103, product "k16_n3"):
- interface 0: boot keyboard (page 1 / usage 6)
- interface 1: composite: keyboard (1/6), mouse (1/2), pointer (1/1), consumer
  (0xC/1), system control (1/0x80), wireless radio (1/0xC)
- interface 2: vendor `ff00/02`, the configuration channel glra-studio uses

The assignment table read on 2026-11-12 (backup taken with glra-studio's CLI):
keys = stock numpad usages (0x53–0x63 area); all three encoders =
push mute (`30 e2`), CW vol+ (`30 e9`), CCW vol− (`30 ea`). With identical codes,
the encoders can't be told apart until `loom:unique-assignments` gives each
action its own code. Captured with Bob at the pad on 2026-11-12 (details and raw logs:
`.loom/threads/midi-mvp/raw-report-capture*/findings.md`):
- keys → interface 0, 8-byte boot reports (`mod 00 k1..k6`), with real press
  and release reports and no device auto-repeat;
- dials → interface 1, report ID 3, consumer usage (3 bytes), release
  `03 00 00`; turn = press+release 1–2 ms apart per detent; push release
  is real (it arrives when let go); fast spins showed no merged detents;
- the vendor interface stays silent in normal use.
Bob holds the pad rotated relative to glra-studio's diagram (dials along the
far edge, it seems), and key 7 in his numbering produced nothing in the capture
passes (dead switch or missed prompt; unresolved as of 2026-11-12).

## Associations
- [[keyboard-seize-needs-root]]
- [[glra-studio-reuse]]
