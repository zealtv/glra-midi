# profile-model: questions for Bob

Raised by Claude (Sonnet worker on `profile-model`), 2026-11-13. Each has the
default taken; the later stitches build on it. All are cheap to change.
`config-app-tour` can put them in front of Bob next to the design's Q1–Q9.

**P1. Layer keys after a layer is removed (design 4.7).** `remove_layer`
renumbers the events on the layers above the removed one, but leaves every
`layer-set` key as it was, as `docs/config-app.md` 4.7 says ("flagged rather
than silently changed"). So with 4 layers, removing layer 2 leaves a
`layer-set 3` key pointing at what used to be layer 4. Only keys pointing past
the new count get flagged (by `validate`). *Default:* the design's rule.
Alternative: renumber `layer-set` targets along with the layers (and flag only
those that pointed at the removed layer).

**P2. Lighting defaults (design 5.2).** The design gives no default for
`brightness` or `speed` when `[lighting]` omits them. *Default:* brightness 4,
speed 2 (the example's values). `dump_profile` always writes all three fields
of `[lighting]`, so a saved file never depends on those defaults.
