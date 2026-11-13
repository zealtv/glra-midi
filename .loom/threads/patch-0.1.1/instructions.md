# patch-0.1.1 — fixes from Bob's tour, after the first release

Bob, 2026-11-13, during the config-app tour: "let's fix those after the release
and make it a version patch bump. same for the other issues i noted earlier,
actually - release first, fix later." So this thread waits on
`public-release/first-release` and ships as 0.1.1 through `release-process`.
Tour answers and evidence: `config-app/config-app-tour.tied/outcome.md`,
`evidence/` here. Device safety from the config-app thread applies: no pad
writes in unattended runs; tests use fakes; the lighting fix gets checked at
the pad with Bob.

Stitches: fix-lighting-readback, fix-quit-crash, layer-removal-renumber,
app-review-polish. Then cut 0.1.1 per `docs/releasing.md` with Bob.
