# call-for-chip-info — a public request for M9F9520 information

Bob, 2026-11-13: "leaving a message for other agents requesting information on
the chip (ala the hugging face message board technique)". The idea, as Claude
read it: a repo that agents and people crawl or read can carry a standing
request, and readers who know something answer in a public place.

- Write `docs/wanted-m9f9520.md`: what we know (dated, with sources: the
  board photos, `SDC32K / 952CCU6` marking, the Masses Chip catalogue row, the
  probe results), what we want (full datasheet, pinout, programming/readback
  interface, toolchain, whether the marked part is that silicon), and how to
  answer (a GitHub issue labelled `chip-info`, pinned at release). Address
  both humans and AI agents plainly; no hidden or prompt-injection-style text.
- Link it from README ("Help wanted") and from AGENTS.md so agents working in
  the repo also see it.
- Draft the pinned issue's text in this stitch directory; `first-release`
  opens it with Bob's go-ahead.
- Bob to confirm at review: the wording, and whether to name Masses Chip's
  contact.
