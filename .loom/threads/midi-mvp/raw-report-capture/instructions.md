# raw-report-capture — learn what the pad actually sends

**Needs Bob at the pad** (pressing keys and turning encoders on cue).
Suggested model: Opus. This is investigative and steers later stitches.

As of 2026-11-12 (see `glean:k16n3-hid-interfaces`) the pad shows three HID
interfaces: 0 = boot keyboard; 1 = composite (keyboard, consumer,
system control, …); 2 = vendor `ff00/02`. A non-exclusive hidapi open of
interfaces 0 and 1 succeeded from Ghostty. The seize probe that showed this lives in
`spike/` beside this file.

With the **current stock assignments** (numpad codes on keys; all three
encoders = mute / vol+ / vol−), capture raw input reports from every
interface, non-exclusively, while Bob works through a scripted sequence:
each key press/hold/release, each encoder CW/CCW slow and fast, each push,
two keys at once, a long hold.

Answer and record (in a `findings.md` in this stitch, then distil into glean):
1. Which interface/report ID carries keyboard usages, which carries consumer
   usages, report lengths and layouts (6KRO? bitmap?).
2. Do keys send a distinct release report? Do encoder pushes? Do encoder
   turns arrive as press+release pairs, and how close together? Does fast
   turning drop or merge steps?
3. Does anything arrive on the vendor interface during normal use?
4. Did the reader get reports without extra macOS permission prompts?
   (Bob would rather not grant Input Monitoring if we can avoid it; record
   exactly what was needed.)

Save representative captures as test fixtures (hex, with labels) for
`event-logger`.
