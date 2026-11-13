# config-design: questions for Bob

Raised by Claude (Opus worker on `config-design`), 2026-11-13. Each has the
default taken; the later stitches build to that default, and
`config-app-tour` puts every one in front of Bob. All are cheap to change
later (a field, a default or a rule in one helper). Sections refer to
`docs/config-app.md`.

**Q1. Latch on CC momentary (2.3).** Today's mapping files have toggled CC
keys (`cc … mode = "toggle"`), which none of the brief's four kinds covers.
*Default:* `cc-momentary` takes `mode = "momentary" | "latch"`, like notes; the
app shows a Latch switch. Alternative: drop latch for CC and convert old
toggled CCs to something else.

**Q2. One ease time for both directions of CC momentary (2.3).** *Default:*
one `ease-ms` and `curve`, used for the rise to high and the fall to low.
Alternative: separate rise and fall times (an attack/release feel).

**Q3. The shipped default profile (2.7).** *Default:* 4 layers; keys play
notes 36–51 on layer 1, 52–67 on 2, 68–83 on 3, 84–99 on 4; dial pushes are
previous layer / layer 1 / next layer; dial turns stay relative CC 16–18 on
all layers. Alternative: one layer, exactly today's mapping.

**Q4. Curve shapes (3.6).** *Default:* quadratic ease-in / ease-out /
ease-in-out. Alternative: cubic (a stronger bend), or a choice of both.

**Q5. Global → per-layer (4.6).** *Default:* the global event is copied to
every layer, so nothing changes until a layer is edited. The goal's earlier
default kept it on the shown layer only and emptied the rest. Which feels
right in use?

**Q6. Lighting mode names and fields (5.1).** *Default:* Claude's names for
modes 4/5 ("Flow (rows)", "Flow (columns)") and 9/10 ("Ripples", "Ripples
2"), and speed offered for every animated mode, brightness for every mode but
Off. These were inferred, not checked mode by mode; direction isn't offered at
all because the probe didn't verify it. Check at the pad on the tour.

**Q7. Where the profile lives (2).** *Default:*
`~/Library/Application Support/glra-osc/profile.toml`, one profile at a time
(Open… / Save As… for others). Alternative: a folder of named profiles with a
picker.

**Q8. Starting layer (3.2).** *Default:* `glra-osc run` starts on layer 1, and
a reload keeps the active layer if it still exists. Alternative: remember the
last layer across runs, or a `start` layer in the profile.
