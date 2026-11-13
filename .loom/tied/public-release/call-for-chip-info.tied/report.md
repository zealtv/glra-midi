# call-for-chip-info: report (worker, 2026-11-13)

## Built

- `docs/wanted-m9f9520.md`: the public request. Sections: why we ask; what we
  know (board, vendor configurator, outside reports, each with who saw it and
  when, and with the open question stated); what we want (seven items, ranked);
  how to answer (GitHub issue labelled `chip-info`); please don't (no
  programmer on `J1`, no firmware for another ID, no neighbour-chip datasheets
  passed off as the real one). It addresses people and AI agents in plain text,
  with no hidden content, and tells agents to consult their user before posting.
- README: one "Help wanted" section before "Licence". AGENTS.md: one "Help
  wanted: chip information" section before "Ownership" (it tells in-repo agents
  to report chip facts to Bob and record them in glean and lore).
- `pinned-issue.md` (this directory): the pinned issue's title and body, with
  the `gh` commands for `first-release` in a header comment.
- `questions.md`: four items for Bob (contact, wording, photos, the label).

Project name and link follow the orchestrator note: glra-midi,
`https://github.com/zealtv/glra-midi`. The doc and issue draft don't mention
glra-osc.

## Not built

- No GitHub label or issue (publishing needs Bob; `first-release` does it).
- No glean finding: the facts already sit in `k16n3-firmware-replacement`.
- No images embedded in the doc (see questions.md, item 3).

## Defaults taken

- Masses Chip's email and phone number stay out of the public doc (stitch left
  it to Bob). The drafted enquiry stays unsent.

## Checks

- Every fact in the doc traces to `glean:k16n3-firmware-replacement`,
  `lore:2026-11-13-k16n3-board-photos`, `lore:2026-11-13-mcu-chip-lead-m9f9520`
  and `lore:2026-11-13-further-chip-findings-m9f9520`. I didn't open the
  catalogue PDF or any external page, and the doc says so.
- `./test.sh` passes (404 tests, 4 skipped), run before the commit and again
  after `git merge main` (already up to date; `rename-code` hadn't landed on
  main when I merged).
- Merge note: when `rename-code` lands, `docs/wanted-m9f9520.md` and the two
  added sections contain no `glra-osc` text, so conflicts should stay limited to
  neighbouring lines in README.md and AGENTS.md.
- `./.glean/glean.sh fetch` warned that `.glean/findings/INDEX.md` is stale; I
  left it alone (not my stitch, no finding changed).

## Open questions

See `questions.md`.
