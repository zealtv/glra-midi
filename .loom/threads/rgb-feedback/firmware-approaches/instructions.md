# firmware-approaches — what routes to our own LED control exist? (sketch)

Sketch; not queued. Bob, 2026-11-13, after choosing route B: "I'd still like to
see what firmware approaches might be possible". Builds on
`glean:k16n3-firmware-replacement` (don't reflash blind; no backup possible).

Candidate approaches to study, cheapest-risk first:
1. **Identify the chip** (Bob is searching; terms in the 2026-11-13 session):
   if the SDCX `9520` turns out to be a known part with a public IDE,
   compiler and programmer, `J1` might become a real recovery path, and both
   own firmware and patching become thinkable.
2. **Patch the stock firmware** (needs 1): add a RAM-only colour command to the
   vendor image. Still needs a flash with no backup unless a programmer can read.
3. **Tap the LED chain**: the 16 LEDs form one WS2812-style chain driven by
   `U1`. An external MCU (RP2040 class) driving `LED1`'s `DI`, with `U1`'s data
   line cut or lifted, would give live per-key control while stock firmware
   keeps keys and encoders. Needs a second USB link (or an internal hub) and
   board surgery; reversible with care.
4. **Replacement controller PCB** in the same case (RP2040/STM32 + QMK/Vial).
Each: risk, reversibility, cost, effort, what it gives `midi-feedback`/`banks`.
